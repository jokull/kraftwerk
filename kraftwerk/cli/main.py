# -*- coding: utf-8 -*-

from __future__ import with_statement

import logging
import os
import argparse

from kraftwerk import templates
from kraftwerk.cli import commands
from kraftwerk.cli.parser import parser
from kraftwerk.config import Config, ConfigNotFound

def create_config(path):
    provider    = raw_input('Provider [rackspace/ec2_eu_west/linode]: ')
    user        = raw_input('Provider user: ')
    secret      = raw_input('Provider secret [optional]: ')
    location_id = raw_input('Provider location [optional]: ')
    image_id    = raw_input('Default Ubuntu image: ')
    size_id     = raw_input('Default node size: ')
    tpl = templates.get_template('.kraftwerk.yaml')
    with open(path, 'w') as fp:
        fp.write(tpl.render({'user': user, 'secret': secret,
            'image_id': image_id, 'size_id': size_id, 
            'provider': provider, 'location_id': location_id }))

def main(cmd_args=None):
    """The main entry point for running the kraftwerk CLI."""
    
    if cmd_args is not None:
        args = parser.parse_args(cmd_args)
    else:
        args = parser.parse_args()
    
    args.config = os.path.abspath(args.config)
    if not os.path.exists(args.config):
        print 'It looks like this is your first time running' \
              'kraftwerk'
        create_config(args.config)
    config = Config.for_file(args.config)
    
    logging.getLogger('kraftwerk').setLevel(getattr(logging, args.log_level))
    command = getattr(commands, args.command.replace('-', '_'))
    return command(config, args)


if __name__ == '__main__':
    main()
