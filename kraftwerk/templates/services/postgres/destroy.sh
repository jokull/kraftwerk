su - postgres -c "psql -c 'DROP DATABASE IF EXISTS {{ project.title }}'"
su - postgres -c "psql -c 'DROP USER IF EXISTS {{ project.title }}'"