import os
import kraftwerk

class BaseService(object):
    
    def __init__(self, node, project):
        self.node = node
        self.project = project
    
    @property
    def setup_script(self):
        module = self.__module__.lower().split('.')[-1]
        template = os.path.join('services', module, 'setup.sh')
        tpl = kraftwerk.templates.get_template(template)
        return tpl.render({'service': self, 'project': self.project})
    
    def load(self):
        raise NotImplementedError
    
    def dump(self):
        raise NotImplementedError
    