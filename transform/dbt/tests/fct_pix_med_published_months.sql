with staged as (
    select ano_mes
    from {{ ref('stg_estatisticas_fraudes_pix') }}
    where ano_mes >= 202201
),
fact as (
    select ano_mes
    from {{ ref('fct_pix_med') }}
)
select ano_mes
from staged
except
select ano_mes
from fact

union all

select ano_mes
from fact
except
select ano_mes
from staged

union all

select ano_mes
from fact
where ano_mes < 202201

union all

select null
from information_schema.columns
where table_schema = 'marts'
    and table_name = 'fct_pix_med'
    and (
        lower(column_name) like '%cautelar%'
        or lower(column_name) like '%bloqueado%'
    )
