-- One row describing how far each dashboard resource has been published.
-- A missing MED month is a sentence, not a zero. The wording is fixed
-- so a dashboard can show it without inventing a month.

with tx as (
    select max(ano_mes) as ano_mes
    from {{ ref('fct_pix_transactions') }}
    where is_complete_month
),
med as (
    select max(ano_mes) as ano_mes
    from {{ ref('fct_pix_med') }}
    where is_complete_month
)
select
    tx.ano_mes as transactions_latest_complete,
    med.ano_mes as med_latest_complete,
    'MED figures are national, monthly, and published 30 days after month-end. Latest month in this extract: '
        || coalesce({{ ano_mes_label('med.ano_mes') }}, 'none') as banner,
    case
        when tx.ano_mes is not null
            and med.ano_mes is not null
            and med.ano_mes < tx.ano_mes
            then {{ month_name('tx.ano_mes') }}
                || ' not published yet; last month is '
                || {{ month_name('med.ano_mes') }}
                || ' '
                || substr(lpad(cast(med.ano_mes as varchar), 6, '0'), 1, 4)
        else cast(null as varchar)
    end as gap_note
from tx
cross join med
