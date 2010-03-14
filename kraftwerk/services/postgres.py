import subprocess

from base import BaseService

class Service(BaseService):
    
    def shell(self, cmd):
        ssh_host = 'root@%s' % self.node
        proc = subprocess.Popen(['ssh', ssh_host, cmd])
        return proc.communicate()
        