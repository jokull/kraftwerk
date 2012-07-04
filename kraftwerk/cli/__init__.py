# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse

from functools import wraps

from ..config import Config
from ..node import Node
from ..project import Project
from ..exc import ConfigError

from .parser import subparsers


CERTIFI_BUNDLE_PATH = None
try:
    # see if requests's own CA certificate bundle is installed
    import certifi
    CERTIFI_BUNDLE_PATH = certifi.where()
except ImportError:
    pass

# common paths for the OS's CA certificate bundle
POSSIBLE_CA_BUNDLE_PATHS = [
        # Red Hat, CentOS, Fedora and friends (provided by the ca-certificates package):
        '/etc/pki/tls/certs/ca-bundle.crt',
        # Ubuntu, Debian, and friends (provided by the ca-certificates package):
        '/etc/ssl/certs/ca-certificates.crt',
        # FreeBSD (provided by the ca_root_nss package):
        '/usr/local/share/certs/ca-root-nss.crt',
]

def get_os_ca_bundle_path():
    """Try to pick an available CA certificate bundle provided by the OS."""
    for path in POSSIBLE_CA_BUNDLE_PATHS:
        if os.path.exists(path):
            return path
    return None

# if certifi is installed, use its CA bundle;
# otherwise, try and use the OS bundle
DEFAULT_CA_BUNDLE_PATH = CERTIFI_BUNDLE_PATH or get_os_ca_bundle_path()

import libcloud.security
libcloud.security.VERIFY_SSL_CERT = True

# optionally, add to CA_CERTS_PATH
libcloud.security.CA_CERTS_PATH.append(DEFAULT_CA_BUNDLE_PATH)


def command(function):
    """Decorator/wrapper to declare a function as a Kraftwerk CLI task."""

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
            proj.validate()
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
            sys.exit("You must specify a 'node' value")
