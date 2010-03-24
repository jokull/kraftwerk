ROOT=/web/{{ project.name }}
export PATH="$ROOT/bin:$PATH"
export PYTHONPATH="$ROOT:$ROOT/lib/python2.6/site-packages:$PYTHONPATH"
{% for key, val in project.environment() -%}
export {{ key }}="{{ val }}"
{% endfor -%}
