from base import BaseService

class Service(BaseService):
    
    @property
    def env(self):
        return dict(UPLOADS_PATH='$ROOT/uploads')