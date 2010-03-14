su - postgres -c "createdb --echo --encoding UTF8 {{ project.title }}"
su - postgres -c "createuser --echo --no-superuser --no-createdb --createrole {{ project.title }}"
su - postgres -c "psql -c 'GRANT ALL PRIVILEGES ON DATABASE {{ project.title }} TO {{ project.title }}'"