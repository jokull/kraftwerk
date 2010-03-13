

class BaseService(object):
    
    def __init__(self, node, project):
        self.node = node
        self.project = project
    
    def setup(self):
        raise NotImplementedError
    
    def load(self):
        raise NotImplementedError
    
    def dump(self):
        raise NotImplementedError
    