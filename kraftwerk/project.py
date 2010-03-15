import os, subprocess, sys
import yaml

from kraftwerk.exc import ConfigError

class Project(object):
    
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.title = os.path.basename(self.path)
        self.src_path = os.path.join(self.path, self.title)
        self._services = None
        with file(os.path.join(self.path, 'kraftwerk.yaml')) as fp:
            self.config = yaml.load(fp.read())
    
    def __unicode__(self):
        return self.title
    
    def load(self, node):
        # TODO
        pass
    
    def dump(self, node):
        # TODO
        pass
    
    def services(self, node, strict=False):
        if self._services:
            return self._services
        self._services = []
        for service in self.config.get('services', []):
            try:
                mod = __import__('kraftwerk.services.' + service, fromlist=[''])
            except ImportError:
                if strict:
                    raise ValueError, 'kraftwerk does not support a %s' % service
            self._services.append(mod.Service(node, self))
        return self._services
    
    def is_valid(self):
        """A best-try attempt at exposing bad config early. Try 
        importing WSGI script, verify some types, required attributes
        etc. """
        sys.path.insert(0, self.path)
        sys.path.insert(0, os.path.join(self.path, 'lib/python2.6/site-packages'))
        wsgi_path = self.config.get('wsgi', '').split(":")
        if not wsgi_path or len(wsgi_path) != 2:
            raise ConfigError, "You must supply a valid wsgi config param (ex: project.wsgi:application)"
        try:
            wsgi_mod = __import__(wsgi_path[0], fromlist=[wsgi_path[0].split(".")[:-1]])
            wsgi_app = getattr(wsgi_mod, wsgi_path[1])
        except ImportError, e:
            raise ConfigError, "WSGI application could not be imported (%s)" % e
        if not callable(wsgi_app):
            raise ConfigError, "WSGI application found but not a callable."
        if not 'workers' in self.config:
            raise ConfigError, "You must specify the number of workers for the WSGI server."
        try:
            int(self.config['workers'])
        except ValueError:
            raise ConfigError, "`workers` value must be a number"
        return True

    def rsync(self, dest):
        cmd = ['rsync',
               '--recursive',
               '--links',         # Copy over symlinks as symlinks
               '--safe-links',    # Don't copy over links that are outside of dir
               '--executability', # Copy +x modes
               '--times',         # Copy timestamp
               '--rsh=ssh',       # Use ssh
               '--delete',        # Delete files thta aren't in the source dir
               '--compress',
               '--exclude-from=%s' % os.path.join(self.path, "rsync_exclude.txt"),
               '--progress',
               '--quiet',
               self.src_path, dest]
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        return proc.communicate()