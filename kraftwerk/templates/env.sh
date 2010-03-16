ROOT=/web/{{ project.title }}
export PATH="$ROOT/bin:$PATH"
export PYTHONPATH="$ROOT:$ROOT/lib/python2.6/site-packages:$PYTHONPATH"
{% for key, val in environment -%}
export {{ key }}="{{ val }}"
{% endfor -%}
