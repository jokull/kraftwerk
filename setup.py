# -*- coding: utf-8 -*-

from __future__ import with_statement

import os, re

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

with open(abspath(join(dirname(__file__), 'requirements.txt')), 'r') as fp:
    # Filter pip-y packages - libcloud has to be installed from git
    requirements = [l.strip() for l in fp if re.match(r'^[\w_-]+$', l.strip())]

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
    install_requires = requirements,
)
