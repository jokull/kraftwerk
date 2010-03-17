# -*- coding: utf-8 -*-

import codecs, logging, os, pprint, sys, re, time, subprocess
from random import choice
from functools import wraps
import argparse
import virtualenv
from libcloud.drivers import ec2, rackspace
# Add as you test support for more providers

import kraftwerk
from kraftwerk import project
from kraftwerk.exc import ConfigError
from kraftwerk.config import path as config_path
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
    def __call__(self, parser, namespace, values, option_string=None):
        if values is None:
            values = os.getcwd()
        try:
            proj = project.Project(os.path.abspath(values))
        except IOError:
            sys.exit("kraftwerk.yaml is missing or project path is " \
                     "not a kraftwerk project directory. \n")
        try:
            proj.is_valid()
        except ConfigError, e:
            print "Project config did not validate: %s" % e
            sys.exit()
        setattr(namespace, self.dest, proj)

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
            dest_path = os.path.join(project_root, rel)
            
            if "project" in dest_path:
                dest_path = dest_path.replace("project", title)
            
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
    
    # Query driver for size and image
    
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
    
    create_info = dict(name=args.hostname,
        image=image, size=size, **extra)
    log.debug("Creating node: %s" % pprint.pprint(create_info))
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
    
    # At least EC2 passes 
    if not IP_RE.match(public_ip):
        from socket import gethostbyname
        public_ip = gethostbyname(public_ip)

    if confirm("Create /etc/hosts entry?"):
        from kraftwerk.etchosts import set_etchosts
        set_etchosts(args.hostname, public_ip)
    
    print "Server ready at %s (%s)" % (args.hostname, public_ip)
    print "Run 'kraftwerk setup-node %s'" % args.hostname
    
create_node.parser.add_argument('hostname', default=None,
    help="Hostname label for the node (optionally adds an entry to /etc/hosts for easy access)")
create_node.parser.add_argument('--size-id',
    help="Provider node size. Defaults to user config.")
create_node.parser.add_argument('--image-name', 
    help="Ubuntu image. Defaults to user config. (ex. EC2 AMI image id)")

@command
def setup_node(config, args):
    """Install software and prepare a node for kraftwerk action."""
    node = getattr(args, "node", config.get("default-node"))
    log = logging.getLogger('kraftwerk.setup-node')
    ssh_host = 'root@%s' % node
    tpl = config.templates.get_template("server_setup.sh")
    proc = subprocess.Popen(['ssh', '-o', 'StrictHostKeyChecking=no',
        ssh_host, tpl.render(dict(config=config))])
    proc.communicate()

setup_node.parser.add_argument('node', default=None, 
    help="Path to the project you want to set up")

@command
def setup_project(config, args):
    """Sync and/or setup a WSGI project. Kraftwerk detects a first-
    time setup and runs service setup."""
    log = logging.getLogger('kraftwerk.setup-project')
    node = getattr(args, "node", config.get("default_node"))
    if node is None:
        sys.exit("Node argument required.")
    ssh_host = 'root@%s' % node
    proc = subprocess.Popen(['ssh', '-o', 'StrictHostKeyChecking=no', 
        ssh_host, 'stat /var/service/%s' % args.project.title], 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.communicate()
    new = bool(proc.returncode) # Could not find the runit script -> new project (TODO: better heuristic)
    
    # Sync codebase over with the web user
    destination = os.path.join('%s:/web/%s/' % 
        ("web@%s" % node, args.project.title))
    stdout, stderr = args.project.rsync(destination)
    if stderr:
        log.error("Sync error: %s" % stderr)
        sys.exit(stderr)
    print "Synced project %s to %s" % (args.project.title, node)
    requirements = os.path.join(args.project.path, 'REQUIREMENTS')
    if os.path.isfile(requirements):
        proc = subprocess.Popen(['scp', requirements, 
            '%s:/web/%s/.' % (ssh_host, args.project.title)], 
            stdout=subprocess.PIPE)
        proc.communicate()
    
    environment = args.project.environment()
    tpl = config.templates.get_template('project_setup.sh')
    cmd = tpl.render(dict(project=args.project, new=new, 
        restart=args.restart, environment=environment, 
        upgrade_packages=args.upgrade_packages))
    proc = subprocess.Popen(['ssh', ssh_host, cmd])
    proc.communicate()
    print "Basic project setup completed (%s to %s)" % (
        args.project.title, node)
    if not args.no_service_setup:
        for service in args.project.services(node):
            proc = subprocess.Popen(['ssh', ssh_host, 
                service.setup_script])
            proc.communicate()

setup_project.parser.add_argument('project', action=ProjectAction,
    nargs='?', 
    help="Path to the project you want to set up. Defaults to current directory.")
    
setup_project.parser.add_argument('--node', required=False, 
    help="Server node to interact with.")
    
setup_project.parser.add_argument('--no-service-setup', 
    default=False, action='store_true',
    help="With this hook kraftwerk overwrites the basic config files but " \
         "does not attempt to set up project services.")

setup_project.parser.add_argument('--upgrade-packages',
    default=False, action='store_true',
    help="Upgrade Python packages (adds -U to pip install)")

setup_project.parser.add_argument('--restart',
    default=False, action='store_true',
    help="Bring down and start the site WSGI service again. Default is to send" \
         "a HUP signal to the process to reload it. ")

@command
def env(config, args):
    """List all project service environment variables, for 
    convenience."""
    tpl = config.templates.get_template("env.sh")
    print tpl.render(dict(project=args.project))

env.parser.add_argument('project', action=ProjectAction, nargs='?',
    help="Path to the project you want to set up. Defaults to current directory.")

@command
def stab(config, args):
    """Execute a shell command in the project environment. Useful for 
    Django syncdb and such."""
    node = getattr(args, "node", config.get("default_node"))
    if node is None:
        sys.exit("Node argument required.")
    ssh_host = 'root@%s' % node
    tpl = config.templates.get_template("env.sh")
    cmd = tpl.render(dict(project=args.project))
    cmd = '\n'.join([cmd, ' '.join(args.c)])
    proc = subprocess.Popen(['ssh', '-o', 'StrictHostKeyChecking=no',
        ssh_host, cmd])
    stdout, stderr = proc.communicate()
    if stderr:
        print u'Error: %s' % stderr
    if stdout:
        print stdout
    

stab.parser.add_argument('project', action=ProjectAction, nargs='?',
    help="Path to the project you want to set up. Defaults to current directory.")
stab.parser.add_argument('--node', required=False, 
    help="Server node to interact with.")
stab.parser.add_argument('-c', nargs='+')



@command
def destroy_project(config, args):
    """Remove project from a node with all related services and 
    files."""
    log = logging.getLogger('kraftwerk.destroy-project')
    node = getattr(args, "node", config.get("default_node"))
    if node is None:
        sys.exit("Node argument required.")
    ssh_host = 'root@%s' % node
    tpl = config.templates.get_template("project_destroy.sh")
    proc = subprocess.Popen(['ssh', '-o', 'StrictHostKeyChecking=no',
        ssh_host, tpl.render(dict(project=args.project))], 
        stdout=subprocess.PIPE)
    proc.communicate()
    print "Project %s removed from node %s" % \
        (args.project.title, node)
    for service in args.project.services(node):
        proc = subprocess.Popen(['ssh', ssh_host, 
            service.destroy_script])
        proc.communicate()


destroy_project.parser.add_argument('project', action=ProjectAction, 
    nargs='?',
    help="Path to the project you want to REMOVE from a server node.")
destroy_project.parser.add_argument('--node', required=False, 
    help="Server node to interact with.")
