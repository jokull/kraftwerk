import subprocess
from socket import gethostbyaddr

class Node(object):
    
    def __init__(self, hostname):
        self.hostname = hostname
    
    def __unicode__(self):
        print self.hostname
    
    @property
    def ip(self):
        return gethostbyaddr(self.hostname)[2][0]
    
    def ssh(self, cmd, user="root", pipe=False, extra={}):
        if pipe:
            extra.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        host = '%s@%s' % (user, self.hostname)
        proc = subprocess.Popen(['ssh', '-A', '-o', 'StrictHostKeyChecking=no', 
            host, cmd], **extra)
        return proc.communicate()