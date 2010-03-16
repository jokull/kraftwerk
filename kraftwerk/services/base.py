import os
import kraftwerk

class BaseService(object):
    
    def __init__(self, project, node):
        self.project = project
        self.node = node
    
    @property
    def name(self):
        return self.__module__.lower().split('.')[-1]
    
    def _script_helper(self, script):
        template = os.path.join('services', self.name, script)
        tpl = kraftwerk.templates.get_template(template)
        return tpl.render({'service': self, 'project': self.project})
    
    @property
    def setup_script(self):
        return self._script_helper('setup.sh')
    
    @property
    def destroy_script(self):
        return self._script_helper('destroy.sh')
    
    def load(self):
        raise NotImplementedError
    
    def dump(self):
        raise NotImplementedError
    
    def env(self):
        return dict()
    