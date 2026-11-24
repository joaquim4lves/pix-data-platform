{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if target.type == 'athena' -%}
        {%- set prefix = env_var('PIX_GLUE_PREFIX', 'pix') -%}
        {%- if custom_schema_name is none or custom_schema_name | trim == '' -%}
            {{ prefix }}_{{ target.schema }}
        {%- else -%}
            {{ prefix }}_{{ custom_schema_name | trim }}
        {%- endif -%}
    {%- elif custom_schema_name is none or custom_schema_name | trim == '' -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
