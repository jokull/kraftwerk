adduser --disabled-password --gecos=none web
mkdir -p /web && cp -R /root/.ssh /home/web/.
chown -R web:web /web /home/web
apt-get -q update
apt-get -y -qq install nginx postgresql python-psycopg2 python-setuptools python-imaging python-lxml python-numpy rsync build-essential subversion git-core unzip zip curl wget redis-server runit mercurial
easy_install virtualenv
cd /usr/local/src && git clone git://github.com/benoitc/gunicorn.git
cd /usr/local/src/gunicorn && python setup.py develop
/usr/sbin/runsvdir-start &>/dev/null & # Background and quiet
mkdir -p /var/service