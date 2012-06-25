# -*- coding: utf-8 -*-

import os
import logging
import jinja2


__version__ = '0.1'

templates_root = os.path.join(os.path.dirname(__file__), 'templates')
templates = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_root))

default_formatter = logging.Formatter(
    u'%(name)s: %(levelname)s: %(message)s')

console_handler = logging.StreamHandler() # By default, outputs to stderr.
console_handler.setFormatter(default_formatter)
console_handler.setLevel(logging.DEBUG)

logging.getLogger('kraftwerk').addHandler(console_handler)
logging.getLogger('kraftwerk').setLevel(logging.INFO) # Default level.


