import subprocess

class Node(object):
    
    def __init__(self, hostname):
        self.hostname = hostname
    
    def __unicode__(self):
        print self.hostname
    
    def ssh(self, cmd, user="root", pipe=False, extra={}):
        if pipe:
            extra.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        host = '%s@%s' % (user, self.hostname)
        proc = subprocess.Popen(['ssh', '-o', 'StrictHostKeyChecking=no', 
            host, cmd], **extra)
        return proc.communicate()