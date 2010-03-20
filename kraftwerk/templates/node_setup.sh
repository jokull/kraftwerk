adduser --disabled-password --gecos=none web
mkdir -p /web && cp -R /root/.ssh /home/web/.
chown -R web:web /web /home/web
apt-get -q update
apt-get -y -qq install build-essential curl git-core mercurial nginx postgresql redis-server rsync runit subversion unzip wget zip
apt-get -y -qq install libevent-dev ncurses-dev python-dev python-imaging python-lxml python-numpy python-psycopg2 python-setuptools
easy_install virtualenv pip gevent readline
# pip install http://github.com/benoitc/gunicorn/tarball/0.6.7
easy_install http://github.com/benoitc/gunicorn/zipball/master
/usr/sbin/runsvdir-start &>/dev/null & # Background and quiet
mkdir -p /var/service

PG_TRUST="local sameuser all trust"
PG_HBA="/etc/postgresql/8.4/main/pg_hba.conf"
if [ "$PG_TRUST" != "`tail -1 $PG_HBA`" ]; then
    echo "$PG_TRUST" >> $PG_HBA
fi

/etc/init.d/nginx start
/etc/init.d/postgresql-8.4 reload
chmod 777 /tmp