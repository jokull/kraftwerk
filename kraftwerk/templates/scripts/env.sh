ROOT=/web/{{ project.name }}

{% for key, val in project.environment() -%}
export {{ key }}="{{ val }}"
{% endfor -%}
