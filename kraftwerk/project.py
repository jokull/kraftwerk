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
        self.src_path = os.path.join(self.path, self.src())
    
    def __unicode__(self):
        return self.name
    
    def src(self):
        return self.config.get('src', self.name)
    
    def dump_path(self, timestamp):
        return '/web/%s/dump/%s/' % (self.name, timestamp)
    
    def dump(self, node):
        timestamp = datetime.now().isoformat().rsplit(".")[0] # '2010-03-23T16:32:22'
        node.ssh("mkdir -p %s" % self.dump_path(timestamp), user="web")
        for service in self.services():
            try:
                service.dump(node, self.dump_path(timestamp))
            except NotImplementedError:
                pass # Report error here? Warning?
        return timestamp
    
    def load(self, node, timestamp):
        for service in self.services():
            try:
                service.load(node, self.dump_path(timestamp))
            except NotImplementedError:
                pass # Report error here? Warning?
    
    def sync_services(self, src_node, dest_node, timestamp=None):
        """
        Uses the dump/load plumbing to transfer project state between
        two nodes. Does a backup dump first, then a dump+transfer on 
        the 'from' node. Destructive.
        ssh-agent is required to do transfers between two nodes.
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
        rsync_cmd = "rsync -e \"ssh -o StrictHostKeyChecking=no\" --recursive --times --archive --compress --delete %s %s" % (rsync_src, rsync_dest)
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
        try:
            file(os.path.join(self.src_path, 'REQUIREMENTS'))
        except IOError:
            raise ConfigError, "REQUIREMENTS file not found - must be under source directory"
        return True

    def rsync(self, dest):
        print dest
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