# -*- coding: utf-8 -*-

import codecs, logging, os, pprint, sys, re, time, subprocess
from random import choice
from functools import wraps

import virtualenv
from libcloud.drivers import ec2, rackspace
# Add as you test support for more providers

import kraftwerk
from kraftwerk.project import Project
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

## Utilities

@command
def show_config(config, args):
    """Pretty-print the current kraftwerk configuration."""
    pprint.pprint(config)

def _copy_project(config, title, project_root):
    
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
                        fp.write(tpl.render({'project': title, 'secret': secret}))

@command
def init(config, args):
    """Initialize a new kraftwerk repository."""
    
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
    log.info('Your new project is at: %s' % project_root)

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
            log.info('SSH public key: %s' % path)
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
            
    size_id = getattr(args, 'size-id', config["size_id"])
    for s in config.driver.list_sizes():
        if s.id == size_id:
            size = s
            break
    
    if isinstance(config.driver, ec2.EC2NodeDriver):
        extra = dict(userdata="""#!/bin/bash
echo '%s' > /root/.ssh/authorized_keys""" % pubkey)
        if not 'keyname' in config:
            raise ValueError, 'ERROR: EC2 "keyname" not found in your config'
        extra.update(keyname=config["keyname"])
        log.debug("ubuntu user will be active and accessible with \
            your %s key" % config["keyname"])
        if 'securitygroup' in config:
            extra.update(securitygroup=config["securitygroup"])
    elif isinstance(config.driver, rackspace.RackspaceNodeDriver):
        extra = dict(files={'/root/.ssh/authorized_keys': pubkey})
    
    create_info = dict(name=args.hostname,
        image=image, size=size, **extra)
    log.debug("Creating node: %s" % pprint.pprint(create_info))
    node = config.driver.create_node(**create_info)
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
    
    log.info("Server ready at %s" % public_ip)

    if confirm("Create /etc/hosts entry?"):
        from kraftwerk.etchosts import set_etchosts
        set_etchosts(args.hostname, public_ip)
    
create_node.parser.add_argument('hostname', default=None,
    help="Hostname label for the node (optionally adds an entry to /etc/hosts for easy access)")
create_node.parser.add_argument('--size-id',
    help="Provider node size. Defaults to user config.")
create_node.parser.add_argument('--image-name', 
    help="Ubuntu image. Defaults to user config. (ex. EC2 AMI image id)")

SETUP_CMD = """adduser --disabled-password --gecos=none web
mkdir -p /web && cp -R /root/.ssh /web/.
chown -R web:web /web
apt-get -q update
apt-get -y -qq install nginx postgresql python-psycopg2 python-setuptools python-imaging python-lxml python-numpy rsync build-essential subversion git-core unzip zip curl wget redis-server runit
easy_install -U gunicorn mercurial
/usr/sbin/runsvdir-start &>/dev/null & # Background and quiet
mkdir -p /var/service"""

@command
def setup_node(config, args):
    """Install software and prepare a node for kraftwerk action."""
    node = getattr(args, "node", config.get("default-node"))
    log = logging.getLogger('kraftwerk.setup-node')
    ssh_host = 'root@%s' % node
    proc = subprocess.Popen(['ssh', '-o', 'StrictHostKeyChecking=no',
        ssh_host, SETUP_CMD])
    proc.communicate()

setup_node.parser.add_argument('node', default=None, 
    help="Path to the project you want to set up")

@command
def setup_project(config, args):
    """Create a project container on a node. Setup all services 
    required. An SSH process is called out once for basic config
    and once for each service. Kraftwerk detects a first-time 
    setup and runs service setup."""
    log = logging.getLogger('kraftwerk.setup-project')
    # Create folders
    # Loop through services setup
    # 
    node = getattr(args, "node", config.get("default-node"))
    if node is None:
        raise ValueError, 'Server node must be supplied as an ' \
                          'argument or in user config.'
    
    project = Project(args.project_path)
    try:
        project.is_valid()
    except Exception, exc:
        print exc
        return
    
    exclude = config.templates.get_template('project/rsync_exclude.txt').render()
    destination = os.path.join('%s:/web/%s/%s' % 
        (node, project.title, project.title))
    log.info("Syncing project")
    project.rsync(destination, exclude)
    
    ssh_host = 'root@%s' % node
    tpl = config.templates.get_template('project_setup.sh')
    cmd = tpl.render(dict(project=project, 
                          services=project.services(node)))
    # print tpl.render(dict(project=project))
    proc = subprocess.Popen(['ssh', ssh_host, cmd])
    proc.communicate()
    services = project.services(node)
    if not args.no_services:
        for service in services:
            proc = subprocess.Popen(['ssh', ssh_host, 
                service.setup_script])
            proc.communicate()

setup_project.parser.add_argument('--node', default=None, 
    help="Server node to interact with. ")
setup_project.parser.add_argument('--project-path', default=os.getcwd(), 
    help="Path to the project you want to set up. Defaults to current directory.")
setup_project.parser.add_argument('--no-services', 
    default=False, action='store_true',
    help="With this hook kraftwerk overwrites the basic config files but " \
         "does not attempt to set up project services.")


