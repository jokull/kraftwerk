import subprocess

from base import BaseService

class MySQL(BaseService):
    
    def command(self, cmd):
        ssh_host = 'root@%s' % self.node
        proc = subprocess.Popen(['ssh', ssh_host, cmd])
        return proc.communicate()
        
    def setup(self):
        print self.command('su postgres createdb -E UTF8 %s -e' % self.project)
        print self.command('su postgres createuser %s -e' % self.project)
        self.command("""su postgres psql -c 
GRANT ALL PRIVILEGES ON DATABASE %s TO %s""" % [self.project]*2)
