# -*- coding: utf-8 -*-

from __future__ import with_statement

from datetime import datetime
import os, subprocess, sys
import yaml

from kraftwerk.exc import ConfigError

def cached_list(f):
    """Decorator that caches yielding methods and stores them as 
    lists.
    
    >>> class A:
    ...    @cached_list
    ...    def ten(self):
    ...        for i in range(10): yield i
    >>> a = A()
    >>> a.ten()
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    >>> a.ten()
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    """
    def func(self, *args, **kwargs):
        key = "%s%s" % (f.__name__, args)
        try:
            return self._property_cache[key]
        except AttributeError:
            self._property_cache = {}
        except KeyError:
            pass
        output = self._property_cache[key] = list(f(self, *args, **kwargs))
        return output
    return func

class Project(object):
    
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.name = os.path.basename(self.path)
        self._services = None
        with file(os.path.join(self.path, 'kraftwerk.yaml')) as fp:
            self.config = yaml.load(fp.read())
            self.name = self.config.get('package', self.name)
        self.src_path = os.path.join(self.path, self.src())
    
    def __unicode__(self):
        return self.name
    
    def src(self):
        return self.config.get('src', self.name)
    
    def dump_path(self, timestamp):
        return '/web/%s/dump/%s/' % (self.name, timestamp)
    
    def dump(self, node):
        timestamp = datetime.now().isoformat().rsplit(".")[0] # '2010-03-23T16:32:22'
        dump_path = self.dump_path(timestamp)
        stdout, stderr = node.ssh("mkdir -p %s" % dump_path, user="web")
        for service in self.services():
            try:
                stdout, stderr = service.dump(node, dump_path)
                if stderr: print stderr
            except NotImplementedError:
                pass # Report error here? Warning?
        return timestamp
    
    def load(self, node, timestamp):
        for service in self.services():
            try:
                stdout, stderr = service.load(node, self.dump_path(timestamp))
                if stderr: print stderr
            except NotImplementedError:
                pass # Report error here? Warning?
    
    def sync_services(self, src_node, dest_node, timestamp=None):
        """
        Uses the dump/load plumbing to transfer project state between
        two nodes. Does a backup dump first, then a dump+transfer on 
        the 'source' node. Destructive. ssh-agent is required to do 
        transfers between two nodes.
        """
        restore_timestamp = self.dump(dest_node) # backup
        if timestamp is None:
            timestamp = self.dump(src_node)
        rsync_src = self.dump_path(timestamp)
        rsync_dest = "root@%s:%s" % (dest_node.ip, rsync_src)
        proc = subprocess.Popen(['ssh-add', '-l'], stdout=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            sys.exit("To use this feature you must be running ssh-agent" + \
                     " with your relevant key added (%s)." % stdout)
        rsync_cmd = "rsync -e \"ssh -o StrictHostKeyChecking=no\" --recursive –-copy-dirlinks --times --archive --compress --delete %s %s" % (rsync_src, rsync_dest)
        stdout, stderr = src_node.ssh(rsync_cmd, user="web", pipe=True)
        if stderr:
            sys.exit("rsync error: %s" % stderr)
        self.load(dest_node, timestamp)
    
    @cached_list
    def services(self, strict=False):
        for service in self.config.get('services', []):
            try:
                mod = __import__('kraftwerk.services.' + service, fromlist=[''])
            except ImportError:
                if strict:
                    raise ValueError, 'kraftwerk does not support a %s' % service
            yield mod.Service(self)
    
    @cached_list
    def environment(self):
        for service in self.services():
            for key, value in service.env.items():
                yield key, value
        if 'environ' in self.config:
            for key, value in self.config['environ'].iteritems():
                yield key, value
    
    def get_split_app_path(self):
        parts = self.config['wsgi'].rsplit(":", 1)
        if len(parts) == 1:
            module, obj = parts[0], "application"
        else:
            module, obj = parts[0], parts[1]
        return module, obj
    
    def _test_app_import(self):
        return True
        from site import addsitedir
        addsitedir(self.path)
        addsitedir(os.path.join(self.path, 'lib/python2.6/site-packages'))
        module, obj = self.get_split_app_path()
        try:
            __import__(module)
            mod = sys.modules[module]
            app = eval(obj, mod.__dict__)
        except Exception, e:
            import traceback
            raise ConfigError, 'Module %r could not be imported\n\n%s' % (module, traceback.format_exc())
        if app is None:
            raise ImportError("Failed to find application object: %r" % obj)
        if not callable(app):
            raise TypeError("Application object must be callable.")
    
    def clean(self):
        """A best-try attempt at exposing bad config early. Try 
        importing WSGI script, verify some types, required attributes
        etc. """
        try:
            assert 'domain' in self.config, "You must specify at least one domain for the nginx configuration."
            assert 'wsgi' in self.config, "You must specify the WSGI app callable (project_name.server:application)."
            assert 'workers' in self.config, "You must specify the number of workers for the WSGI server."
        except AssertionError, e:
            raise ConfigError, unicode(e)
        self._test_app_import()
        if ' ' in self.config['domain']:
            raise ConfigError, "Domain must be a string or a list of strings"
        try:
            int(self.config['workers'])
        except ValueError:
            raise ConfigError, "`workers` value must be a number"
        try:
            file(os.path.join(self.path, 'requirements.txt'))
        except IOError:
            raise ConfigError, "requirements.txt file not found - must be under source directory"
        self.config['module'], \
        self.config['callable'] = self.get_split_app_path()
        return True

    def rsync(self, dest):
        exclude = os.path.join(self.path, "rsync_exclude.txt")
        cmd = ['rsync',
               '--recursive',
               '--links',         # Copy over symlinks as symlinks
               '--safe-links',    # Don't copy over links that are outside of dir
               '--executability', # Copy +x modes
               '--times',         # Copy timestamp
               '--rsh=ssh',       # Use ssh
               '--delete',        # Delete files thta aren't in the source dir
               '--compress',
               '--progress',
               '--quiet',
               self.src_path, dest]
        if os.path.isfile(exclude):
            cmd.insert(1, '--exclude-from=%s' % exclude)
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        return proc.communicate()
    
    def canonical_domain(self):
        if isinstance(self.config['domain'], basestring):
            return self.config['domain']
        else:
            return self.config['domain'][0]