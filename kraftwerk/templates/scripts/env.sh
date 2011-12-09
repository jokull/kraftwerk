ROOT=/web/{{ project.name }}
export PATH="$ROOT/bin:$PATH"

PYTHON_VERSION=$(python -c 'import sys; print ".".join(map(str, sys.version_info)[:2])')
VIRTUALENV_SITEPACKAGES="$ROOT/lib/python$PYTHON_VERSION/site-packages"

{% for key, val in project.environment() -%}
export {{ key }}="{{ val }}"
{% endfor -%}
