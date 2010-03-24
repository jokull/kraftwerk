# -*- coding: utf-8 -*-

from __future__ import with_statement

import codecs, logging, os, pprint, sys, re, time, subprocess
from random import choice
from functools import wraps
import argparse
import virtualenv
from libcloud.drivers import ec2, rackspace, linode
# Add as you test support for more providers

import kraftwerk
from kraftwerk.project import Project
from kraftwerk.node import Node
from kraftwerk.exc import ConfigError
from kraftwerk.config import Config, path as config_path
from kraftwerk.cli.parser import subparsers
from kraftwerk.cli.utils import confirm
from kraftwerk import etchosts
from kraftwerk import services

IP_RE = re.compile(r'(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})')

def command(function):
    """Decorator/wrapper to declare a function as a kraftwerk CLI task."""
    
    cmd_name = function.__name__.replace('_', '-')
    help = (function.__doc__ or '').rstrip('.') or None
    parser = subparsers.add_parser(cmd_name, help=help)
    
    @wraps(function)
    def wrapper(config, args):
        logging.getLogger('kraftwerk').debug('Running kraftwerk.%s' % cmd_name)
        return function(config, args)
    wrapper.parser = parser
    
    return wrapper

class ProjectAction(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        if value is None:
            value = os.getcwd()
        try:
            proj = Project(os.path.abspath(value))
        except IOError:
            sys.exit("kraftwerk.yaml is missing or project path is " \
                     "not a kraftwerk project directory. \n")
        try:
            proj.is_valid()
        except ConfigError, e:
            print "Project config did not validate: %s" % e
            sys.exit()
        setattr(namespace, self.dest, proj)

class NodeAction(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        if value is None:
            config = Config.for_file(namespace.config)
            if "default_node" in config:
                value = config["default_node"]
                print "Using default_node (%s)" % value
        if value:
            setattr(namespace, self.dest, Node(value))
        else:
            sys.exit("No node value found")
            

## Utilities

@command
def show_config(config, args):
    """Pretty-print the current kraftwerk configuration."""
    pprint.pprint(config)

def _copy_project(config, title, project_root):
    """`init` helper to push the project skeleton through templates 
    and copy over."""
    
    secret = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
    start = os.path.join(kraftwerk.templates_root, 'project')
    
    for dirpath, dirnames, filenames in os.walk(start):
        # Copy template skeleton
        for name in dirnames + filenames:
            
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, start)
            
            project_rel = rel
            if "project" in rel:
                project_rel = rel.replace("project", title)

            dest_path = os.path.join(project_root, project_rel)

            if not os.path.exists(dest_path):
                if os.path.isdir(path):
                    os.makedirs(dest_path)
                else:
                    with codecs.open(dest_path, 'w', encoding='utf-8') as fp:
                        tpl = config.templates.get_template(os.path.join('project', rel))
                        fp.write(tpl.render({'project_title': title, 'secret': secret}))

@command
def init(config, args):
    """Create a new WSGI project skeleton and config."""
    
    log = logging.getLogger('kraftwerk.init')
    
    # project_root/src_root
    project_root = os.path.abspath(os.path.join(os.getcwd(), args.title))
    src_root = os.path.join(project_root, args.title)
    
    if os.path.exists(project_root) and os.listdir(project_root):
        init.parser.error("Directory exists and isn't empty")
    elif not os.path.exists(project_root):
        log.debug('makedirs %s' % project_root)
        os.makedirs(project_root)
    elif not os.path.isdir(project_root):
        init.parser.error("A file with this name already exists here and isn't a directory")
    
    log.debug('virtualenv %s/' % args.title)
    logger = virtualenv.Logger([
                 (virtualenv.Logger.level_for_integer(2), sys.stdout)])
    virtualenv.logger = logger
    virtualenv.create_environment(args.title, site_packages=True)
    
    log.debug('mkdir %s/service/' % project_root)
    os.makedirs(os.path.join(args.title, 'service'))
    log.debug('mkdir %s/static/' % project_root)
    os.makedirs(os.path.join(args.title, 'static'))
    log.debug('mkdir %s/' % src_root)
    os.makedirs(src_root)
    
    _copy_project(config, args.title, project_root)
    print "Your new project is at: %s" % project_root

init.parser.add_argument('title', default=None,
    help="Create kraftwerk project (if omitted, defaults to current directory)")


@command
def create_node(config, args):
    """Commissions a new server node."""
    log = logging.getLogger('kraftwerk.create-node')
    
    pubkey_paths = [os.path.join(os.environ['HOME'], '.ssh', f) for f \
        in ['id_rsa.pub', 'id_dsa.pub']]
    if 'pubkey' in config:
        pubkey_paths.append(config["pubkey"])
    for path in pubkey_paths:
        if os.path.exists(path):
            print 'SSH public key: %s' % path
            with open(path) as fp:
                pubkey = fp.read().strip()
            break
    else:
        pubkey = raw_input('Your SSH public key (for root login): ')
    
    if not re.search(r'^[a-z0-9.-]+$', args.hostname):
        raise CommandError(
            "Invalid hostname (must contain only letters, numbers, ., and -): %r"
            % args.hostname)
    
    # Query driver for size, image, and location
    
    image_id = getattr(args, 'image-id', config["image_id"])
    for i in config.driver.list_images():
        if i.id == image_id:
            image = i
            break
    else:
        sys.exit("Image %s not found for this provider. Aborting." % image_id)
            
    size_id = getattr(args, 'size-id', config["size_id"])
    for s in config.driver.list_sizes():
        if s.id == size_id:
            size = s
            break
    else:
        sys.exit("Size %s not found for this provider. Aborting." % size_id)
    
    location_id = getattr(args, 'location-id', config.get("location_id", 0))
    for l in config.driver.list_locations():
        if l.id == location_id:
            location = l
            break
    else:
        sys.exit("Location %s not found for this provider. Aborting." % location_id)
    
    if isinstance(config.driver, ec2.EC2NodeDriver):
        extra = dict(userdata="""#!/bin/bash
echo '%s' > /root/.ssh/authorized_keys""" % pubkey)
        if not "keyname" in config:
            config["keyname"] = raw_input("EC2 Key Pair [default=\"default\"]: ") or "default"
        extra.update(keyname=config["keyname"])
        if 'securitygroup' in config:
            extra.update(securitygroup=config["securitygroup"])
    elif isinstance(config.driver, rackspace.RackspaceNodeDriver):
        extra = dict(files={'/root/.ssh/authorized_keys': pubkey})
    elif isinstance(config.driver, linode.LinodeNodeDriver):
        from libcloud.base import NodeAuthSSHKey
        extra = dict(auth=NodeAuthSSHKey(pubkey))
    
    create_info = dict(name=args.hostname, location=location,
        image=image, size=size, **extra)
    try:
        node = config.driver.create_node(**create_info)
    except Exception, e:
        raise Exception, "libcloud error: %s" % e
    public_ip = node.public_ip[0]
    
    # Poll the node until it has a public ip
    while not public_ip:
        time.sleep(3)
        nodes = filter(lambda n: node.id == n.id, config.driver.list_nodes())
        if nodes:
            public_ip = nodes[0].public_ip[0]
    
    # At least EC2 passes only back hostname
    if not IP_RE.match(public_ip):
        from socket import gethostbyname
        public_ip = gethostbyname(public_ip)

    if confirm("Create /etc/hosts entry?"):
        from kraftwerk.etchosts import set_etchosts
        set_etchosts(args.hostname, public_ip)
    
    print u"Node %s (%s)" % (args.hostname, public_ip)
    print u"Run 'kraftwerk setup-node %s'" % args.hostname
    
create_node.parser.add_argument('hostname', default=None,
    help="Hostname label for the node (optionally adds an entry to /etc/hosts for easy access)")
create_node.parser.add_argument('--size-id',
    help="Provider node size. Defaults to user config.")
create_node.parser.add_argument('--image-name', 
    help="Ubuntu image. Defaults to user config. (ex. EC2 AMI image id)")

@command
def setup_node(config, args):
    """Install software and prepare a node for kraftwerk action."""
    stdin, stderr = args.node.ssh(config.template("node_setup.sh"))
    if stderr:
        print stderr
    else:
        print u"Node ready at %s" % (args.node.hostname)
    
setup_node.parser.add_argument('node', action=NodeAction, 
    help="Server node to interact with.")

@command
def deploy(config, args):
    """Sync and/or setup a WSGI project. Kraftwerk detects a first-
    time setup and runs service setup."""
    log = logging.getLogger('kraftwerk.deploy')
    
    stdout, stderr = args.node.ssh('stat /var/service/%s' % args.project.name, pipe=True)
    new = bool(stderr)
    
    # Sync codebase over with the web user
    destination = 'web@%s:/web/%s/' % (args.node.hostname, args.project.name)
    stdout, stderr = args.project.rsync(destination)
    if stderr:
        log.error("Sync error: %s" % stderr)
        sys.exit(stderr)
        
    if args.sync_only:
        return
    
    # Put together the setup script
    cmd = config.template("project_setup.sh", 
        project=args.project, new=new, 
        restart=args.restart, 
        upgrade_packages=args.upgrade_packages)
    args.node.ssh(cmd)
    
    # TODO detect new services
    if not args.no_service_setup and new:
        for service in args.project.services():
            args.node.ssh(service.setup_script)
            
    print u"%s live at %r" % (args.project.config["domain"], args.node.hostname)
    
deploy.parser.add_argument('node', action=NodeAction, nargs='?',
    help="Server node to interact with.")

deploy.parser.add_argument('project', action=ProjectAction,
    nargs='?', 
    help="Project root directory path. Defaults to current directory.")
    
deploy.parser.add_argument('--no-service-setup', 
    default=False, action='store_true',
    help="With this hook kraftwerk overwrites the basic config files but " \
         "does not attempt to set up project services.")

deploy.parser.add_argument('--upgrade-packages',
    default=False, action='store_true',
    help="Upgrade Python packages (adds -U to pip install)")

deploy.parser.add_argument('--restart',
    default=False, action='store_true',
    help="Bring down and start the site WSGI service again. Default is to send" \
         "a HUP signal to the process to reload it. ")
         
deploy.parser.add_argument('--sync-only',
    default=False, action='store_true',
    help="Only sync files across and exit. Quicker if you don't need to reload Python code.")


@command
def destroy(config, args):
    """Remove project from a node with all related services and 
    files."""
    log = logging.getLogger('kraftwerk.destroy')
    if confirm("Remove project %s from node %s along with all services and data?" % 
            (args.project.name, args.node.hostname)):
        args.node.ssh(config.template("project_destroy.sh", project=args.project))
        print "Project %s removed from node %s" % \
            (args.project.name, args.node)
        for service in args.project.services(args.node):
            args.node.ssh(service.destroy_script)

destroy.parser.add_argument('node', action=NodeAction, nargs='?',
    help="Server node to interact with.")

destroy.parser.add_argument('project', action=ProjectAction, 
    nargs='?',
    help="Path to the project you want to REMOVE from a server node.")


@command
def stab(config, args):
    """Execute a shell command in the project environment. Useful for 
    django-admin.py syncdb and such."""
    
    cmd = config.template("env.sh", project=args.project)
    cmd = '\n'.join([cmd, ' '.join(args.script)])
    args.node.ssh(cmd, user=args.user)
    
    
stab.parser.add_argument('node', action=NodeAction, nargs='?',
    help="Server node to interact with.")

stab.parser.add_argument('project', action=ProjectAction, nargs='?', 
    help="Project root directory path. Defaults to current directory.")

stab.parser.add_argument('--script', '-s', nargs='+', required=True)

stab.parser.add_argument('--user', '-u', help="User to login and issue command as.", default="web")


@command
def dump(config, args):
    """Create a copy of all service data. Reports a directory with all 
    dump files."""
    timestamp = args.project.dump(args.node)
    print "Dump ready at %s:%s" % (args.node.hostname, 
        args.project.dump_path(timestamp))
    
dump.parser.add_argument('node', action=NodeAction, nargs='?',
    help="Server node to interact with.")

dump.parser.add_argument('project', action=ProjectAction, nargs='?', 
    help="Project root directory path. Defaults to current directory.")

@command
def load(config, args):
    """Load a timestamped dumpdir from the same node. (No support yet
    for user provided dumps). To load data from another node use
    `sync-services`."""
    if not args.no_backup:
        timestamp = args.project.dump(args.node)
        print "Pre-load backup: %s" % args.project.dump_path(timestamp)
    args.project.load(args.node, args.timestamp)
    print "Service data from %s loaded at %s" % (args.timestamp, 
        args.node.hostname) 
    
load.parser.add_argument('node', action=NodeAction, nargs='?',
    help="Server node to interact with.")

load.parser.add_argument('timestamp', 
    help="ISO 8601 timestamp. This is the dir name inside " \
    "/web/project/dump to load data from. (Example: 2010-03-24T15:42:54)")

load.parser.add_argument('project', action=ProjectAction, nargs='?', 
    help="Project root directory path. Defaults to current directory.")
         
load.parser.add_argument('--no-backup', default=False, action='store_true',
    help="Only sync files across and exit. Quicker if you don't need to reload Python code.")

@command
def sync_services(config, args):
    """Snapshot service data and restore on another node. This is a 
    destructive action. Kraftwerk does an additional dump before 
    loading new data just in case."""
    timestamp = args.project.sync_services(args.srcnode, args.destnode)
    
sync_services.parser.add_argument('srcnode', action=NodeAction, 
    help="Server node to dump data from.")
    
sync_services.parser.add_argument('destnode', action=NodeAction, 
    help="Server node to load data into.")

sync_services.parser.add_argument('project', action=ProjectAction, nargs='?', 
    help="Project root directory path. Defaults to current directory.")

@command
def env(config, args):
    """List all project service environment variables, for 
    convenience."""
    print config.template("env.sh", project=args.project)

env.parser.add_argument('project', action=ProjectAction, nargs='?',
    help="Project root directory path. Defaults to current directory.")
