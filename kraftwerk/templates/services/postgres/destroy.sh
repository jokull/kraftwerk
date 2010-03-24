su - postgres -c "psql -c 'DROP DATABASE IF EXISTS {{ project.name }}'"
su - postgres -c "psql -c 'DROP USER IF EXISTS {{ project.name }}'"