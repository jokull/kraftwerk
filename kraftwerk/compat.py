"""
os.path.relpath was introduced in Python 2.6. A posix-only implementation
from the Python 2.6 source is provided here. It's used if we can't import
an implementation from the system. The original implementation is released
under the Python Software Foundation License Version 2
"""
use_system_version = False

try:
    from os.path import relpath
    use_system_version = True
except ImportError:
    pass

if not use_system_version:

    from os.path import abspath, join

    curdir = '.'
    sep = '/'
    pardir = '..'

    def commonprefix(m):
        "Given a list of pathnames, returns the longest common leading component"
        if not m: return ''
        s1 = min(m)
        s2 = max(m)
        for i, c in enumerate(s1):
            if c != s2[i]:
                return s1[:i]
        return s1

    def relpath(path, start=curdir):
        """Return a relative version of a path"""

        if not path:
            raise ValueError("no path specified")

        start_list = abspath(start).split(sep)
        path_list = abspath(path).split(sep)

        # Work out how much of the filepath is shared by start and path.
        i = len(commonprefix([start_list, path_list]))

        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return curdir
        return join(*rel_list)
