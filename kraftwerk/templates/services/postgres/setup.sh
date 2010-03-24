su - postgres -c "createdb --echo --encoding UTF8 {{ project.name }}"
su - postgres -c "createuser --echo --no-superuser --no-createdb --createrole {{ project.name }}"
su - postgres -c "psql -c 'GRANT ALL PRIVILEGES ON DATABASE {{ project.name }} TO {{ project.name }}'"