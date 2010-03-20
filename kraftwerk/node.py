import subprocess

class Node(object):
    
    def __init__(self, hostname):
        self.hostname = hostname
    
    def __unicode__(self):
        print self.hostname
    
    def ssh(self, cmd, user="root", stdout=subprocess.PIPE, stderr=subprocess.PIPE):
        host = '%s@%s' % (user, self.hostname)
        proc = subprocess.Popen(['ssh', '-o', 'StrictHostKeyChecking=no', 
            host, cmd], stdout=stdout, stderr=stderr)
        return proc.communicate()