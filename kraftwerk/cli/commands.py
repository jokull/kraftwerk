# -*- coding: utf-8 -*-

import codecs, logging, os, pprint, sys
from random import choice
from functools import wraps

import jinja2
import virtualenv

import kraftwerk
from kraftwerk.config import path as config_path
from kraftwerk.cli.parser import subparsers

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

def _project_template(title, project_root):
    
    templates_dir = os.path.join(kraftwerk.templates_dir, 'project')
    template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))
    secret = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
    
    for dirpath, dirnames, filenames in os.walk(templates_dir):
        # Copy template skeleton
        for name in dirnames + filenames:
            
            template_path = os.path.join(dirpath, name)
            base_path = os.path.relpath(template_path, templates_dir)
            dest_path = os.path.join(project_root, base_path)
            
            if "project" in dest_path:
                dest_path = dest_path.replace("project", title)
            
            if not os.path.exists(dest_path):
                if os.path.isdir(template_path):
                    os.makedirs(dest_path)
                else:
                    with codecs.open(dest_path, 'w', encoding='utf-8') as fp:
                        template = template_env.get_template(base_path)
                        fp.write(template.render({'project': title, 'secret': secret}))
    

@command
def init(config, args):
    """Initialize a new kraftwerk repository."""
    
    log = logging.getLogger('kraftwerk.init')
    
    if not args.title:
        log.info('No title specified; using current directory')
        title = os.path.basename(os.getcwd())
    else:
        title = args.title
    
    # project_root/src_root
    project_root = os.path.join(os.getcwd(), title)
    src_root = os.path.join(project_root, title)
    
    if os.path.exists(project_root) and os.listdir(project_root):
        init.parser.error("Directory exists and isn't empty")
    elif not os.path.exists(project_root):
        log.debug('makedirs %s' % project_root)
        os.makedirs(project_root)
    elif not os.path.isdir(project_root):
        init.parser.error("A file with this name already exists here and isn't a directory")
    
    log.debug('virtualenv %s/' % title)
    logger = virtualenv.Logger([
                 (virtualenv.Logger.level_for_integer(2), sys.stdout)
             ])
    virtualenv.logger = logger
    virtualenv.create_environment(title, site_packages=True)
    
    log.debug('mkdir %s/service/' % project_root)
    os.makedirs(os.path.join(title, 'service'))
    log.debug('mkdir %s/static/' % project_root)
    os.makedirs(os.path.join(title, 'static'))
    log.debug('mkdir %s/' % src_root)
    os.makedirs(src_root)
    
    _project_template(title, project_root)
    
    log.info('Project initialization complete')
    log.info('Your new project is at: %s' % title)

init.parser.add_argument('title', default=None,
    help="Create kraftwerk project (if omitted, defaults to current directory)")

