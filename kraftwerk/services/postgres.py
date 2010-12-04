from os.path import join

from base import BaseService

class Service(BaseService):
    
    @property
    def env(self):
        return {
            'POSTGRES_USER': self.project.name,
            'POSTGRES_DATABASE': self.project.name}
    
    def _dump_path(self, path):
        return join(path, 'postgresql.db.out')
    
    def dump(self, node, path):
        return node.ssh('pg_dump --username=%s --file=%s -F c %s' % (
            self.env['POSTGRES_USER'], 
            self._dump_path(path), 
            self.env['POSTGRES_DATABASE']), pipe=True, user="web")
    
    def load(self, node, path):
        return node.ssh('su - postgres -c "pg_restore --username=postgres --dbname=%s --clean -F c %s"' % (
            self.env['POSTGRES_DATABASE'], 
            self._dump_path(path)), pipe=True)