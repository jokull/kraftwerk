ROOT=/web/{{ project.name }}
export PATH="$ROOT/bin:$PATH"
VIRTUALENV_SITEPACKAGES="$ROOT/lib/`ls -1 $ROOT/lib`/site-packages"
# Trick to get python2.5 and python2.6
{% for key, val in project.environment() -%}
export {{ key }}="{{ val }}"
{% endfor -%}
