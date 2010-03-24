PROJECT={{ project.name }}
rm -rf /web/$PROJECT
rm -rf /{etc,var}/service/$PROJECT
rm /etc/nginx/sites-enabled/$PROJECT
/etc/init.d/nginx reload