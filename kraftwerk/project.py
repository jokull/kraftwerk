import os
import yaml

class Project(object):
    
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.title = os.path.basename(self.path)
        with file(os.path.join(self.path, 'kraftwerk.yaml')) as fp:
            self.config = yaml.load(fp.read())
    
    def load(self, node):
        # TODO
        pass
    
    def dump(self, node):
        # TODO
        pass

    def update(self, node):
        dest_dir = os.path.join('/web', instance_name)
        exclude_from = os.path.join(os.path.dirname(__file__), 'rsync-exclude.txt')
        cmd = ['rsync',
               '--recursive',
               '--links',         # Copy over symlinks as symlinks
               '--safe-links',    # Don't copy over links that are outside of dir
               '--executability', # Copy +x modes
               '--times',         # Copy timestamp
               '--rsh=ssh',       # Use ssh
               '--delete',        # Delete files thta aren't in the source dir
               '--compress',
               #'--skip-compress=.zip,.egg', # Skip some already-compressed files
               '--exclude-from=%s' % exclude_from,
               '--progress',
               '--quiet',
               self.dir,
               os.path.join('%s:%s' % (host, dest_dir)),
               ]
        proc = subprocess.Popen(cmd)
        proc.communicate()