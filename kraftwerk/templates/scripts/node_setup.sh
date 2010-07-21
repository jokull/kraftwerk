{% include 'scripts/pre_node_setup.sh' %}
adduser --disabled-password --gecos=none web
mkdir -p /web && cp -R /root/.ssh /home/web/.
chown -R web:web /web /home/web
apt-get -q update
apt-get -y -qq install build-essential curl git-core mercurial nginx postgresql rsync runit subversion unzip wget zip rabbitmq-server
apt-get -y -qq install libevent-dev ncurses-dev python-dev python-imaging python-lxml python-numpy python-psycopg2 python-setuptools
easy_install virtualenv pip gevent setproctitle
/usr/sbin/runsvdir-start &>/dev/null & # Background and quiet
mkdir -p /var/service

PG_HBA="/etc/postgresql/8.4/main/pg_hba.conf"
cat > $PG_HBA << "EOF"
{% include 'conf/pg_hba.conf' %}
EOF

/etc/init.d/nginx start
/etc/init.d/postgresql-8.4 reload
chmod 777 /tmp
{% include 'scripts/post_node_setup.sh' %}