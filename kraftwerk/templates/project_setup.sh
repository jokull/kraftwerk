PROJECT="{{ project.title }}"
SITE_SERVICE="/etc/service/$PROJECT"

{% if new -%}
virtualenv /web/$PROJECT
chown web:web /web/$PROJECT
{%- endif %}

{% if project.config.packages %}
/web/$PROJECT/bin/pip install{% if upgrade_packages %} -U{% endif %} -r /web/$PROJECT/REQUIREMENTS
{% endif %}

cat > /etc/nginx/sites-enabled/$PROJECT << "EOF"
{% include 'nginx.conf' %}
EOF

mkdir -p /var/service/$PROJECT
cat > /var/service/$PROJECT/run << "EOF"
{% include 'gunicorn.sh' %}
EOF

{% if new -%}
ln -s /var/service/$PROJECT $SITE_SERVICE
chmod +x $SITE_SERVICE/run
{% else %}
  {%- if restart -%}
sv restart $SITE_SERVICE
  {%- else %}
sv hup $SITE_SERVICE
  {%- endif -%}
{%- endif %}

/etc/init.d/nginx reload