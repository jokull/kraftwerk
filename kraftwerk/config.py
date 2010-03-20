# -*- coding: utf-8 -*-

from __future__ import with_statement

import copy
import yaml
import os
import jinja2

from libcloud.types import Provider
from libcloud.base import ConnectionUserAndKey, ConnectionKey
from libcloud.providers import get_driver as libcloud_get_driver

from kraftwerk import templates_root
from kraftwerk.exc import ConfigError

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
    
    """
    
    __metaclass__ = ConfigMeta
    
    def __init__(self, config_file, config):
        super(Config, self).__init__(flatten(config))
        self.driver = self._driver
        self.templates = self._templates
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
        try:
            driver = DriverClass(*credentials)
        except TypeError, e:
            raise ConfigError, 'API Access credentials for %s provider ' \
                               'are missing or wrong' % self['provider']
        return driver
    
    @property
    def _templates(self):
        loaders = [jinja2.FileSystemLoader(templates_root)]
        if "templates" in self:
            loaders.insert(0, jinja2.FileSystemLoader(self["templates"]))
        return jinja2.Environment(loader=jinja2.ChoiceLoader(loaders))
    
    @classmethod
    def for_file(cls, filename):
        """Get the configuration from a given YAML file."""
        
        if not os.path.exists(filename):
            relpath = os.path.relpath(os.path.dirname(filename), start=os.getcwd())
            basename = os.path.basename(filename)
            if relpath == '.':
                raise ConfigNotFound("%s was not found in the current directory" % basename)
            raise ConfigNotFound("%s was not found in %s" % (basename, relpath))
        
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
            for key2 in value.keys():
                value2 = value.pop(key2)
                if not isinstance(value2, dict):
                    dictionary[prefix + key + '.' + key2] = value2
                else:
                    dictionary.update(flatten(value2,
                        prefix=(prefix + key + '.' + key2 + '.')))
    return dictionary