import os
import yaml

class Project(object):
    
    def __init__(self, path):
        self.path = os.path.abspath(path)
        with file(os.path.join(self.path, 'kraftwerk.yaml')) as fp:
            self.config = yaml.load(fp.read())
    
    def load(self, node):
        # TODO
    
    def dump(self, node):
        # TODO