{% include 'scripts/pre_node_setup.sh' %}
adduser --disabled-password --gecos=none web
mkdir -p /web && cp -R /root/.ssh /home/web/.
chown -R web:web /web /home/web

locale-gen en_US.UTF-8

apt-get -q update
apt-get -y -qq upgrade
apt-get -y -qq install curl git-core mercurial nginx postgresql rsync runit unzip wget zip nginx htop redis-server
apt-get -y -qq install build-essential libxml2-dev libevent-dev ncurses-dev python-dev python-imaging python-lxml python-numpy python-psycopg2 python-setuptools

easy_install virtualenv pip uwsgi
mkdir -p /var/service

POSTGRESQL_VERSION=$(apt-cache policy postgresql | grep -Eow "[0-9]\.[0-9]" | head -1)

PG_HBA="/etc/postgresql/$POSTGRESQL_VERSION/main/pg_hba.conf"
cat > $PG_HBA << "EOF"
{% include 'conf/pg_hba.conf' %}
EOF

/usr/sbin/runsvdir-start &>/dev/null & # Background and quiet
/etc/init.d/nginx start
/etc/init.d/postgresql restart
chmod 777 /tmp

{% include 'scripts/post_node_setup.sh' %}