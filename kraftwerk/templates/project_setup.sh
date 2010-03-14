{% if new %}

{% endif %}

mkdir -p /web/{{ project.title }}
chown web:web /web/{{ project.title }}
cat > /etc/nginx/sites-enabled/{{ project.title }} << "EOF"
{% include 'nginx.conf' %}

EOF
/etc/init.d/nginx reload
/etc/init.d/nginx start
mkdir -p /var/service/{{ project.title }}
cat > /var/service/{{ project.title }}/run << "EOF"
{% include 'gunicorn.sh' %}

EOF
chmod +x /var/service/run
ln -s /var/service/{{ project.title }} /etc/service/{{ project.title }}