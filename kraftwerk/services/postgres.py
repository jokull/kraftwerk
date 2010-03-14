import subprocess

from base import BaseService

class Service(BaseService):
    
    def shell(self, cmd):
        ssh_host = 'root@%s' % self.node
        proc = subprocess.Popen(['ssh', ssh_host, cmd])
        return proc.communicate()
    
    def env(self):
        return dict(
            USER=self.project.title,
            PASSWORD=self.project.title,
            DATABASE=self.project.title)
        