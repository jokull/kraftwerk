ROOT=/web/{{ project.name }}
export PATH="$ROOT/bin:$PATH"
# Trick to get python2.5 and python2.6
{% for key, val in project.environment() -%}
export {{ key }}="{{ val }}"
{% endfor -%}
