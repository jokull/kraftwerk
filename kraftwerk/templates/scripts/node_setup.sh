{% include 'scripts/pre_node_setup.sh' %}
adduser --disabled-password --gecos=none web
mkdir -p /web && cp -R /root/.ssh /home/web/.
chown -R web:web /web /home/web

locale-gen en_US.UTF-8

cat > /etc/default/locale << "EOF"
LANG="en_US.UTF-8"
LANGUAGE="en_US.UTF-8"
LC_ALL="en_US.UTF-8"
EOF

source /etc/default/locale

apt-get -q update
apt-get -y -qq upgrade
apt-get -y -qq install curl git-core mercurial nginx postgresql rsync runit unzip wget zip nginx htop redis-server
apt-get -y -qq install build-essential libxml2-dev libevent-dev ncurses-dev python-dev python-imaging python-lxml python-numpy python-psycopg2 python-setuptools

easy_install virtualenv pip uwsgi
mkdir -p /var/service

POSTGRESQL_VERSION=$(apt-cache policy postgresql | grep -Eow "[0-9]\.[0-9]" | head -1)

pg_createcluster $POSTGRESQL_VERSION main --start

PG_HBA="/etc/postgresql/$POSTGRESQL_VERSION/main/pg_hba.conf"
cat > $PG_HBA << "EOF"
{% include 'conf/pg_hba.conf' %}
EOF

/usr/sbin/runsvdir-start &>/dev/null & # Background and quiet
/etc/init.d/nginx start
/etc/init.d/postgresql restart
chmod 777 /tmp

{% include 'scripts/post_node_setup.sh' %}