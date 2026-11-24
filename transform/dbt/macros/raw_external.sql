{% macro raw_external(name) %}
    {%- if target.type == 'duckdb' -%}
        (
            select
                *,
                {{ raw_loaded_at(name) }} as _loaded_at
            from read_parquet(
                getvariable('pix_raw_{{ name }}'),
                hive_partitioning=true,
                union_by_name=true
            )
        )
    {%- else -%}
        unused
    {%- endif -%}
{% endmacro %}

{% macro raw_loaded_at(name) %}
    {%- if name.startswith('app_') -%}
        cast(commit_ts as timestamp)
    {%- else -%}
        cast(
            concat(
                substr(lpad(cast(ano_mes as varchar), 6, '0'), 1, 4),
                '-',
                substr(lpad(cast(ano_mes as varchar), 6, '0'), 5, 2),
                '-01'
            ) as timestamp
        )
    {%- endif -%}
{% endmacro %}
