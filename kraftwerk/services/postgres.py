import subprocess

from base import BaseService

class Service(BaseService):
    
    def env(self):
        return {
            'POSTGRES_USER': self.project.title,
            'POSTGRES_DATABASE': self.project.title}