from __future__ import with_statement

"""This script is adapted from Ian Bicking's Silver Lining project
which is under GPLv2 licensing."""

"""Handle /etc/hosts

This has methods to put a new host->ip setting in /etc/hosts, as well
as get a setting from that file.

As /etc/hosts can only be edited by root, this ultimately calls out to
sudo to do the actual edit. The script actually calls itself with sudo 
from the command line (which runs main()).
"""

import os, time, subprocess

def set_etchosts(hostname, ip):
    """Sets a line in /etc/hosts to assign the hostname to the ip

    This may add or edit to the file, or do nothing if is already set.
    It will call a subcommand with sudo if necessary to edit.
    """
    with open('/etc/hosts') as fp:
        for line in fp.read().splitlines():
            line = line.strip()
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.split()
            line_ip = parts[0]
            line_hosts = parts[1:]
            if line_ip == ip:
                if hostname in line_hosts:
                    hostname.remove(hostname)
                    return
            force_update = False
            if hostname in line_hosts:
                force_update = True
                break
            if force_update:
                break

    cmd = ["sudo", "python", __file__, ip, hostname]
    proc = subprocess.Popen(cmd)
    proc.communicate()

def main(ip, hostname):
    """Add the hostname->ip relation to the given file (typically /etc/hosts)
    """
    with open('/etc/hosts') as fp:
        lines = list(fp)
    new_lines = []
    for line in lines:
        if not line.strip() or line.strip().startswith('#'):
            new_lines.append(line)
            continue
        line_ip, hostnames = line.strip().split(None, 1)
        hostnames = hostnames.split()
        if hostname in hostnames:
            if line_ip == ip:
                # Everything is okay... (odd)
                return
            # Oh no, we have to kill that!
            hostnames = hostnames.remove(hostname)
            if hostnames:
                new_lines.append('%s %s' % (line_ip, ' '.join(hostnames)))
            else:
                if new_lines and new_lines[-1].startswith('# kraftwerk'):
                    new_lines.pop()
        else:
            new_lines.append(line)
    new_lines.append('# kraftwerk alias set at %s:\n'
                     % time.strftime('%c'))
    new_lines.append('%s %s\n' % (ip, hostname))
    with open('/etc/hosts', 'w') as fp:
        fp.writelines(new_lines)

if __name__ == '__main__':
    import sys
    ip = sys.argv[1]
    hostnames = sys.argv[2:]
    for hostname in hostnames:
        main(ip, hostname)
    

    
