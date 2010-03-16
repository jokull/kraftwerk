from base import BaseService

class Service(BaseService):
    def env(self):
        return dict(UPLOADS_PATH='$ROOT/uploads')