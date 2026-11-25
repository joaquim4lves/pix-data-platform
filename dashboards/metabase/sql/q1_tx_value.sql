select month_start, sum(valor) as settled_value
from marts.fct_pix_transactions
where is_complete_month
group by month_start
order by month_start
