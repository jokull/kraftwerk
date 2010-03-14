# -*- coding: utf-8 -*-

import logging
import os, shutil
import argparse

from kraftwerk.cli import commands
from kraftwerk.cli.parser import parser
from kraftwerk.config import Config, ConfigNotFound

def create_config(path):
    provider = raw_input('Provider [rackspace/ec2_eu_west]: ')
    user     = raw_input('Your provider user/accesskey: ')
    secret   = raw_input('Your provider secret: ')
    image_id = raw_input('Your default Ubuntu image: ')
    size_id  = raw_input('Your default node size: ')
    tpl = config.templates.get_template('.kraftwerk.yaml')
    with open(path, 'w') as fp:
        fp.write(tpl.render({'user': user, 'secret': secret,
            'image_id': image_id, 'size_id': size_id, 'provider': provider }))

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