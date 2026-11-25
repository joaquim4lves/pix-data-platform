select
    month_start,
    sum(valor) as settled_value,
    cast(round(sum(quantidade)) as bigint) as transactions
from marts.fct_pix_transactions
where is_complete_month
[[and {{period}}]]
group by month_start
order by month_start
