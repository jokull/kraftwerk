import subprocess

from base import BaseService

class Service(BaseService):
    
    def env(self):
        return dict(
            POSTGRES_USER=self.project.title,
            POSTGRES_PASSWORD=self.project.title,
            POSTGRES_DATABASE=self.project.title)