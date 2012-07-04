# -*- coding: utf-8 -*-

from __future__ import with_statement

import sys

from setuptools import setup, find_packages

from kraftwerk import __version__


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
    author           = "Jokull Solberg Audunsson",  # Jökull Sólberg Auðunsson
    author_email     = "jokull@solberg.is",
    description      = "A WSGI deployment CLI",
    license          = "BSD",
    url              = "http://www.kraftwerk-wsgi.com/",
    zip_safe         = False,
    packages         = find_packages(),
    include_package_data = True,
    entry_points     = {'console_scripts': ['kraftwerk = kraftwerk.cli.main:main']},
    install_requires = requires,
)
