ROOT=/web/{{ project.name }}
export PATH="$ROOT/bin:$PATH"
VIRTUALENV_SITEPACKAGES="$ROOT/lib/`ls -1 $ROOT/lib`/site-packages"
# Trick to get python site-packages folder regardless of version
# TODO this fails
{% for key, val in project.environment() -%}
export {{ key }}="{{ val }}"
{% endfor -%}
