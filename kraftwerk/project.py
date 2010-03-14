import os, subprocess, sys
import yaml

class ValidationError(Exception):
    pass

class Project(object):
    
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.title = os.path.basename(self.path)
        self.src_path = os.path.join(self.path, self.title)
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
        _services = []
        for service in self.config.get('services', []):
            try:
                mod = __import__('kraftwerk.services.' + service, fromlist=[''])
            except ImportError:
                if strict:
                    raise ValueError, 'kraftwerk does not support a %s' % service
            _services.append(mod.Service(node, self))
        return _services
    
    def is_valid(self):
        sys.path.insert(0, self.path)
        sys.path.insert(0, os.path.join(self.path, 'lib/python2.6/site-packages'))
        wsgi_path = self.config.get('wsgi', '').split(":")
        if not wsgi_path or len(wsgi_path) != 2:
            raise ValidationError, "You must supply a valid wsgi config param (ex: project.wsgi:application)"
        wsgi_mod = __import__(wsgi_path[0], fromlist=[wsgi_path[0].split(".")[:-1]])
        wsgi_app = getattr(wsgi_mod, wsgi_path[1])
        if not callable(wsgi_app):
            raise ValidationError, "WSGI application found but not a callable."
        if not 'workers' in self.config:
            raise ValidationError, "You must specify the number of workers for the WSGI server."
        try: int(self.config['workers'])
        except TypeError: raise ValidationError, "Workers value must be a number"
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