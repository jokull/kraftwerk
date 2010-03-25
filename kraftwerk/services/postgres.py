from os.path import join

from base import BaseService

class Service(BaseService):
    
    @property
    def env(self):
        return {
            'POSTGRES_USER': self.project.name,
            'POSTGRES_DATABASE': self.project.name}
    
    def _dump_path(self, path):
        return join(path, 'sql.tar.gz')
    
    def dump(self, node, path):
        return node.ssh('pg_dump --username=%s --file=%s --format=c %s' % (
            self.env['POSTGRES_USER'], 
            self._dump_path(path), 
            self.env['POSTGRES_DATABASE']), pipe=True)
    
    def load(self, node, path):
        return node.ssh('su - postgres -c "pg_restore --username=postgres --dbname=%s --clean --format=c %s"' % (
            self.env['POSTGRES_DATABASE'], 
            self._dump_path(path)), pipe=True)