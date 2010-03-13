# -*- coding: utf-8 -*-

import logging
import os, shutil
import argparse

from kraftwerk import templates_dir
from kraftwerk.cli import commands
from kraftwerk.cli.parser import parser
from kraftwerk.config import Config, ConfigNotFound
    
def main(cmd_args=None):
    """The main entry point for running the kraftwerk CLI."""
    
    if cmd_args is not None:
        args = parser.parse_args(cmd_args)
    else:
        args = parser.parse_args()
    
    try:
        args.config = os.path.abspath(args.config)
        
        if not os.path.exists(args.config):
            print 'It looks like this is your first time running' \
                  'kraftwerk'
            # TODO query for config params
            template = os.path.join(templates_dir, 
                os.path.basename(args.config))
            shutil.copy(template, args.config)
        config = Config.for_file(args.config)
    except Exception, exc:
        print str(exc)
        raise ConfigNotFound("Couldn't locate kraftwerk config.")
    
    logging.getLogger('kraftwerk').setLevel(getattr(logging, args.log_level))
    
    command = getattr(commands, args.command.replace('-', '_'))
    return command(config, args)


if __name__ == '__main__':
    main()