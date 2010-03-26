ROOT=/web/{{ project.name }}
export PATH="$ROOT/bin:$PATH"
# Trick to get python2.5 and python2.6
PYTHON=`ls -1 $ROOT/lib | grep python`
export PYTHONPATH="$ROOT:$ROOT/lib/$PYTHON/site-packages:$PYTHONPATH"
{% for key, val in project.environment() -%}
export {{ key }}="{{ val }}"
{% endfor -%}
