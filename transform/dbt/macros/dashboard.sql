{% macro pix_as_of_date() %}
    {%- set configured = var('pix_as_of_date', '') -%}
    {%- if configured -%}
        cast('{{ configured }}' as date)
    {%- else -%}
        cast(current_timestamp - interval '3' hour as date)
    {%- endif -%}
{% endmacro %}

{% macro is_complete_month(ano_mes_expr) %}
    ({{ ano_mes_expr }} < (year({{ pix_as_of_date() }}) * 100 + month({{ pix_as_of_date() }})))
{% endmacro %}

{% macro month_start(ano_mes_expr) %}
    cast(
        concat(
            substr(lpad(cast({{ ano_mes_expr }} as varchar), 6, '0'), 1, 4),
            '-',
            substr(lpad(cast({{ ano_mes_expr }} as varchar), 6, '0'), 5, 2),
            '-01'
        ) as date
    )
{% endmacro %}

{% macro ano_mes_label(ano_mes_expr) %}
    (
        substr(lpad(cast({{ ano_mes_expr }} as varchar), 6, '0'), 1, 4)
        || '-'
        || substr(lpad(cast({{ ano_mes_expr }} as varchar), 6, '0'), 5, 2)
    )
{% endmacro %}

{% macro month_name(ano_mes_expr) %}
    case cast({{ ano_mes_expr }} % 100 as integer)
        when 1 then 'January'
        when 2 then 'February'
        when 3 then 'March'
        when 4 then 'April'
        when 5 then 'May'
        when 6 then 'June'
        when 7 then 'July'
        when 8 then 'August'
        when 9 then 'September'
        when 10 then 'October'
        when 11 then 'November'
        when 12 then 'December'
        else 'Unknown'
    end
{% endmacro %}

{% macro dashboard_label(raw_expr, fold_outros=true) %}
    case
        when {{ raw_expr }} is null then 'Unstated / other'
        when upper(trim(cast({{ raw_expr }} as varchar))) in (
            'NAO INFORMADO',
            'NÃO INFORMADO',
            'NAO DISPONIVEL',
            'NÃO DISPONÍVEL',
            'N/D',
            'ND',
            'NA',
            'N/A',
            'NAO SE APLICA',
            'NÃO SE APLICA'
            {%- if fold_outros -%}
            , 'OUTROS'
            {%- endif -%}
        ) then 'Unstated / other'
        else trim(cast({{ raw_expr }} as varchar))
    end
{% endmacro %}

{% macro label_with_token(raw_expr, fold_outros=true) %}
    case
        when {{ raw_expr }} is null then 'Unstated / other'
        when {{ dashboard_label(raw_expr, fold_outros) }} = 'Unstated / other'
            then 'Unstated / other (' || trim(cast({{ raw_expr }} as varchar)) || ')'
        else trim(cast({{ raw_expr }} as varchar))
    end
{% endmacro %}
