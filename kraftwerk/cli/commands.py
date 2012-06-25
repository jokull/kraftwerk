# -*- coding: utf-8 -*-

from __future__ import with_statement

import logging
import os
import pprint
import sys
import re
import time

from random import choice
from socket import gethostbyname

from libcloud.compute.drivers import ec2, rackspace, linode

from .. import etchosts

from .utils import confirm
from . import command, NodeAction, ProjectAction

IP_RE = re.compile(r'(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})')
            

## Utilities

@command
def show_config(config, args):
    """Pretty-print the current kraftwerk configuration."""
    pprint.pprint(config)


@command
def create_node(config, args):
    """Commissions a new server node."""
    log = logging.getLogger('kraftwerk.create-node')
    
    if 'pubkey' in config:
        pubkey_paths = [config["pubkey"]]
    else:
        pubkey_paths = [os.path.join(os.environ['HOME'], '.ssh', f) for f \
            in ['id_rsa.pub', 'id_dsa.pub']]

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
    print args
    print dir(args)
    image_id = args.image_id or config['image_id']
    for i in config.driver.list_images():
        if str(i.id) == image_id:
            image = i
            break
    else:
        sys.exit("Image %s not found for this provider. Aborting." % image_id)
    
    size_id = args.size_id or config['size_id']
    for s in config.driver.list_sizes():
        if str(s.id) == size_id:
            size = s
            break
    else:
        sys.exit("Size %s not found for this provider. Aborting." % size_id)
        
    location_id = str(getattr(args, 'location-id', config.get("location_id", "0")))
    if location_id != 'None':
        for l in config.driver.list_locations():
            if str(l.id) == location_id:
                location = l
                break
        else:
            sys.exit("Location %s not found for this provider. Aborting." % location_id)
    else:
        location = None
    
    if isinstance(config.driver, ec2.EC2NodeDriver):
        extra = dict(ex_userdata="""#!/bin/bash
echo '%s' > /root/.ssh/authorized_keys""" % pubkey)
        if not "keyname" in config:
            config["keyname"] = raw_input("EC2 Key Pair [default=\"default\"]: ") or "default"
        extra.update(ex_keyname=config["keyname"])
        if 'securitygroup' in config:
            extra.update(ex_securitygroup=config["securitygroup"])
    elif isinstance(config.driver, rackspace.RackspaceNodeDriver):
        extra = dict(ex_files={'/root/.ssh/authorized_keys': pubkey})
    elif isinstance(config.driver, linode.LinodeNodeDriver):
        from libcloud.base import NodeAuthSSHKey
        extra = dict(auth=NodeAuthSSHKey(pubkey))
    
    create_info = dict(name=args.hostname, location=location,
        image=image, size=size, **extra)
    node = config.driver.create_node(**create_info)
    public_ip = node.public_ip
    
    # Poll the node until it has a public ip
    while not public_ip:
        time.sleep(3)
        for node_ in config.driver.list_nodes():
            if node.id == node_.id and node_.public_ip:
                public_ip = node_.public_ip[0]

    if type(public_ip) == list:
        public_ip = public_ip[0]

    # At least EC2 passes only back hostname
    if not IP_RE.match(public_ip):
        public_ip = gethostbyname(public_ip)

    if confirm("Create /etc/hosts entry?"):
        etchosts.set_etchosts(args.hostname, public_ip)
    
    print u"Node %s (%s)" % (args.hostname, public_ip)
    print u"Run 'kraftwerk setup-node %s'" % args.hostname
    
create_node.parser.add_argument('hostname', default=None,
    help="Hostname label for the node (optionally adds an entry to /etc/hosts for easy access)")
create_node.parser.add_argument('--size-id', 
    help="Provider node size. Defaults to user config.")
create_node.parser.add_argument('--image-id', 
    help="Ubuntu image. Defaults to user config. (ex. EC2 AMI image id)")

@command
def setup_node(config, args):
    """Install software and prepare a node for kraftwerk action."""
    if args.templates:
        config['templates'].insert(0, args.templates)
        config.templates = config._templates()
    stdin, stderr = args.node.ssh(config.template("scripts/node_setup.sh"))
    if stderr:
        print stderr
    else:
        print u"Node ready at %s" % (args.node.hostname)
    
setup_node.parser.add_argument('node', action=NodeAction, 
    help="Server node to interact with.")

setup_node.parser.add_argument('--templates', 
    help="External template directory. These will take precedence over "
        "kraftwerk and user templates. You can use this to save and "
        "organize setup recipes.")
    

@command
def deploy(config, args):
    """Sync and/or setup a WSGI project. Kraftwerk detects a first-
    time setup and runs service setup."""
    log = logging.getLogger('kraftwerk.deploy')
    
    # TODO better way to detect new, or maybe move to dedicated command
    stdout, stderr = args.node.ssh('stat /var/service/%s' % args.project.name, pipe=True)
    new = bool(stderr) or args.override
    
    # Sync codebase over with the web user
    destination = 'web@%s:/web/%s/' % (args.node.hostname, args.project.name)
    stdout, stderr = args.project.rsync(destination)
    if stderr:
        log.error("Sync error: %s" % stderr)
        sys.exit(stderr)
    
    # Copy requirements
    args.project.copy(args.node, 'requirements.txt')
    
    # Put together the setup script
    cmd = config.template("scripts/project_setup.sh", 
        project=args.project, new=new, 
        upgrade_packages=args.upgrade_packages)
    stdout, stderr = args.node.ssh(cmd, pipe=True)
    if stderr:
        print stderr
    
    # TODO detect new services
    if not args.no_service_setup and new:
        for service in args.project.services():
            args.node.ssh(service.setup_script)
            
    print u"%s live at %r" % (args.project.canonical_domain(), args.node.hostname)
    
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
         
deploy.parser.add_argument('--override',
    default=False, action='store_true',
    help="Create folders and config as if deploying for the first time.")


@command
def destroy(config, args):
    """Remove project from a node with all related services and 
    files."""
    log = logging.getLogger('kraftwerk.destroy')
    if confirm("Remove project %s from node %s along with all services and data?" % 
            (args.project.name, args.node.hostname)):
        args.node.ssh(config.template("scripts/project_destroy.sh", project=args.project))
        print "Project %s removed from node %s" % \
            (args.project.name, args.node.hostname  )
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
    
    cmd = config.template("scripts/env.sh", project=args.project)
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
    if not confirm("WARNING: This isn't considered production ready just yet. Continue?"):
        return
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
def env(config, args):
    """List all project service environment variables, for 
    convenience."""
    print config.template("scripts/env.sh", project=args.project)

env.parser.add_argument('project', action=ProjectAction, nargs='?',
    help="Project root directory path. Defaults to current directory.")
