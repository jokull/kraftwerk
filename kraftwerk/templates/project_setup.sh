mkdir /web/{{ project.title }} > /dev/null
chown web:web /web/{{ project.title }}
cat > /nginx/sites-enabled/{{ project.title }} <<
{% include 'nginx.conf' %}
EOF
/etc/init.d/nginx reload