# -*- coding: utf-8 -*-

import os
import argparse
from kraftwerk import config

parser = argparse.ArgumentParser(**{
    'prog': 'kraftwerk',
    'description': 'A WSGI deployment automation tool.',
})

config = parser.add_argument('--config', '-c', default=config.path,
    help="Use the specified kraftwerk config (a YAML file")

log_level = parser.add_argument('--log-level', '-l', metavar='LEVEL',
    default='INFO', choices='DEBUG INFO WARN ERROR'.split(),
    help="Choose a log level from DEBUG, INFO (default), WARN or ERROR")

quiet = parser.add_argument('--quiet', '-q',
    action='store_const', dest='log_level', const='ERROR',
    help="Alias for --log-level ERROR")

verbose = parser.add_argument('--verbose',
    action='store_const', dest='log_level', const='DEBUG',
    help="Alias for --log-level DEBUG")

subparsers = parser.add_subparsers(dest='command', title='commands', metavar='COMMAND')