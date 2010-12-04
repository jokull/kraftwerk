{% include 'scripts/pre_node_setup.sh' %}
adduser --disabled-password --gecos=none web
mkdir -p /web && cp -R /root/.ssh /home/web/.
chown -R web:web /web /home/web

echo "deb http://ppa.launchpad.net/nginx/stable/ubuntu maverick main" >> /etc/apt/sources.list
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys C300EE8C
apt-get -q update
apt-get -q upgrade
apt-get -y -qq install curl git-core mercurial nginx postgresql rsync runit subversion unzip wget zip nginx
apt-get -y -qq install build-essential libxml2-dev libevent-dev ncurses-dev python-dev python-imaging python-lxml python-numpy python-psycopg2 python-setuptools

easy_install virtualenv pip gevent setproctitle uwsgi
mkdir -p /var/service

PG_HBA="/etc/postgresql/8.4/main/pg_hba.conf"
cat > $PG_HBA << "EOF"
{% include 'conf/pg_hba.conf' %}
EOF

/usr/sbin/runsvdir-start &>/dev/null & # Background and quiet
/etc/init.d/nginx start
/etc/init.d/postgresql restart
chmod 777 /tmp
{% include 'scripts/post_node_setup.sh' %}