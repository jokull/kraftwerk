adduser --disabled-password --gecos=none web
mkdir -p /web && cp -R /root/.ssh /home/web/.
chown -R web:web /web /home/web
apt-get -q update
apt-get -y -qq install nginx postgresql python-psycopg2 python-setuptools python-imaging python-lxml python-numpy rsync build-essential subversion git-core unzip zip curl wget redis-server runit mercurial
easy_install virtualenv pip
pip install http://github.com/benoitc/gunicorn/tarball/0.6.7
/usr/sbin/runsvdir-start &>/dev/null & # Background and quiet
mkdir -p /var/service
echo 'local sameuser all trust' >> /etc/postgresql/8.4/main/pg_hba.conf
/etc/init.d/nginx start
/etc/init.d/postgresql-8.4 reload