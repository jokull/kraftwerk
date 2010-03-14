su postgres createdb -E UTF8 {{ project.title }} -e
su postgres createuser {{ project.title }} -e
su postgres psql -c GRANT ALL PRIVILEGES ON DATABASE {{ project.title }} TO {{ project.title }}