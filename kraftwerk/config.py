# -*- coding: utf-8 -*-

from __future__ import with_statement

import copy
import yaml
import os
import jinja2

from libcloud.compute.types import Provider
from libcloud.compute.base import ConnectionUserAndKey, ConnectionKey
from libcloud.compute.providers import get_driver as libcloud_get_driver
from libcloud.compute.drivers import ec2, rackspace, linode

import libcloud.security
libcloud.security.VERIFY_SSL_CERT = False

from kraftwerk import templates_root
from kraftwerk.exc import ConfigError
from kraftwerk.compat import relpath

path = os.path.join(os.path.expanduser('~'), '.kraftwerk.yaml')

class ConfigNotFound(Exception):
    """The configuration file was not found."""
    pass


class ConfigMeta(type):
    
    def __new__(mcls, name, bases, attrs):
        cls = type.__new__(mcls, name, bases, attrs)
        cls._defaults = {}
        cls._func_defaults = {}
        return cls
    
    def register_default(cls, key, default_value):
        """Register a default value for a given key."""
        
        cls._defaults[key] = default_value
    
    def register_func_default(cls, key, function):
        """Register a callable as a functional default for a key."""
        
        cls._func_defaults[key] = function
    
    def func_default_for(cls, key):
        """Decorator to define a functional default for a given key."""
        
        return lambda function: [cls.register_func_default(key, function),
                                 function][1]


class Config(dict):
    
    """
    A dictionary which represents a system wide kraftwerk configuration.
    
    When instantiating this dictionary, if you aren't using an actual
    configuration file, just remember to set `config['meta.root']` to the
    project root; you can use `None` as the value for config_file. For example:
        
        # With a filename:
        config = Config('filename.yaml', {...})
        
        # Without a filename:
        config = Config(None, {'meta': {'root': '/path/to/wiki/root/'}, ...})
    
    Config additionally passes the template environment and the libcloud 
    driver.
    
    Config as a `template` key and a `template` attribute. The key is
    the user configured templates folder path. The attribute is a jinja2
    template environment with a cascade of loaders. The `_template` 
    method is used to calculate and recalculate the correct loader.
    
    """
    
    __metaclass__ = ConfigMeta
    
    def __init__(self, config_file, config):
        super(Config, self).__init__(flatten(config))
        self.driver = self._driver
        if isinstance(self.get('templates'), basestring):
            self['templates'] = [self['templates']]
        self.templates = self._templates()
        self['meta.config-file'] = config_file
    
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if key in self._defaults:
                self[key] = copy.copy(self._defaults[key])
            elif key in self._func_defaults:
                self[key] = self._func_defaults[key](self, key)
            else:
                raise
            return dict.__getitem__(self, key)
    
    def __delitem__(self, key):
        if (key not in self):
            return # fail silently.
        return dict.__delitem__(self, key)
    
    def template(self, name, **context):
        return self.templates.get_template(name).render(dict(self, **context))
    
    @property
    def _driver(self):
        provider = self['provider']
        DriverClass = libcloud_get_driver(getattr(Provider, provider.upper()))
        credentials = [self['user']]
        if issubclass(DriverClass.connectionCls, ConnectionUserAndKey):
            credentials.append(self['secret'])
        if issubclass(DriverClass, ec2.EC2NodeDriver):
            # Respect AWS environment variables
            user_key, secret_key = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")
            if all (k in os.environ for k in (user_key, secret_key)):
                credentials = os.environ[user_key], os.environ[secret_key]
        try:
            driver = DriverClass(*credentials)
        except TypeError, e:
            raise ConfigError, 'API Access credentials for %s provider ' \
                               'are missing or wrong' % self['provider']
        return driver
    
    def _templates(self):
        loaders = [jinja2.FileSystemLoader(templates_root)]
        # Prepend additional directories
        # We can call this method again after appending 
        project_template_dir = os.path.join(os.getcwd(), 'templates')
        if os.path.exists(project_template_dir):
            loaders.insert(0, jinja2.FileSystemLoader(project_template_dir))
        if "templates" in self:
            for path in self['templates']:
                templates = os.path.expanduser(path)
                loaders.insert(0, jinja2.FileSystemLoader(templates))
        return jinja2.Environment(loader=jinja2.ChoiceLoader(loaders))
    
    @classmethod
    def for_file(cls, filename):
        """Get the configuration from a given YAML file."""
        
        if not os.path.exists(filename):
            relative = relpath(os.path.dirname(filename), start=os.getcwd())
            basename = os.path.basename(filename)
            if relative == '.':
                raise ConfigNotFound("%s was not found in the current directory" % basename)
            raise ConfigNotFound("%s was not found in %s" % (basename, relative))
        
        with open(filename) as fp:
            config = yaml.load(fp) or {}
        
        return cls(filename, config)


def flatten(dictionary, prefix=''):
    
    """
    Flatten nested dictionaries into dotted keys.
    
        >>> d = {
        ...     'a': {
        ...           'b': 1,
        ...           'c': {
        ...                 'd': 2,
        ...                 'e': {
        ...                       'f': 3
        ...                 }
        ...           }
        ...      },
        ...      'g': 4,
        ... }
    
        >>> sorted(flatten(d).items())
        [('a.b', 1), ('a.c.d', 2), ('a.c.e.f', 3), ('g', 4)]
    """
    
    for key in dictionary.keys():
        value = dictionary.pop(key)
        if not isinstance(value, dict):
            dictionary[prefix + key] = value
        else:
            dictionary.update(flatten(value, prefix=(prefix + key + '.')))
    return dictionary
