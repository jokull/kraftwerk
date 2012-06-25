# -*- coding: utf-8 -*-

from __future__ import with_statement

import os, re, sys

from os.path import join, dirname, abspath, curdir
from setuptools import setup, find_packages

from kraftwerk import __version__
from kraftwerk.compat import relpath

def find_package_data():
    files = []
    src_root = join(dirname(__file__), 'kraftwerk')
    static_root = join(src_root, 'templates')
    for dirpath, subdirs, filenames in os.walk(static_root):
        for filename in filenames:
            if not filename.startswith('.') or filename.startswith('_'):
                abs_path = join(dirpath, filename)
                files.append(relpath(abs_path, start=src_root))
    return files

requires = [
    "apache-libcloud>=0.7.1",
    "Jinja2>=2.6",
    "PyYAML>=3.10",
    "virtualenv>=1.7",
    "certifi>=0.0.7",
]

if sys.version_info < (2, 7): 
    requires.append('argparse>=1.2.1') 

setup(
    name             = 'kraftwerk',
    version          = __version__,
    author           = "Jokull Solberg Audunsson", # Jökull Sólberg Auðunsson
    author_email     = "jokull@solberg.is",
    description      = "A WSGI deployment CLI",
    license          = "BSD",
    url              = "http://www.kraftwerk-wsgi.com/",
    zip_safe         = False,
    packages         = find_packages(),
    package_data     = {'kraftwerk': find_package_data()},
    include_package_data = True,
    entry_points     = {'console_scripts': ['kraftwerk = kraftwerk.cli.main:main']},
    install_requires = requires,
)
