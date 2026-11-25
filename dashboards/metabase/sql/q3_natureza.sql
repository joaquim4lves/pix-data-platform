select
    month_start,
    natureza,
    case
        when {{measure}} = 'count' then sum(quantidade)
        else sum(valor)
    end as amount
from marts.fct_pix_transactions
where is_complete_month
[[and {{period}}]]
group by month_start, natureza
order by month_start, natureza
