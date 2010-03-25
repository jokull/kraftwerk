from os.path import join

from base import BaseService

class Service(BaseService):
    
    @property
    def env(self):
        return dict(UPLOADS_PATH='/web/%s/uploads' % self.project.name)
    
    def _dump_path(self, path):
        return join(path, 'uploads')
    
    def dump(self, node, path):
        return node.ssh('cp -R %s %s' % (self.env['UPLOADS_PATH'], 
            self._dump_path(path)))
    
    def load(self, node, path):
        """Uses symlinks to switch the uploads directory as atomically
        as possible."""
        cmd = """mv %(uploads)s %(old_uploads)s
                 ln -s %(old_uploads)s %(uploads)s
                 cp -R %(dump)s %(new_uploads)s
                 mv %(new_uploads)s %(uploads)s
                 rm -rf %(old_uploads)s""" % dict(
            uploads=self.env['UPLOADS_PATH'],
            dump=self._dump_path(path),
            old_uploads=join(self.project.path, 'old_uploads'),
            new_uploads=join(self.project.path, 'new_uploads'))
        return node.ssh(cmd)


