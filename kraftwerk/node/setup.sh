adduser --disabled-password --gecos=none web
mkdir -p /web && cp -R /root/.ssh /web/.
chown -R web:web /web
git clone git://github.com/benoitc/gunicorn.git /usr/local/src/gunicorn &
apt-get install postgresql-server nginx python-setuptool python-pil python-lxml python-numpy \
    rsync build-essential postfix subversion git-core unzip zip curl wget redis runit
/usr/sbin/runsvdir-start &
mkdir /var/service