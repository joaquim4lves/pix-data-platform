select month_start, cast(round(sum(quantidade)) as bigint) as transactions
from marts.fct_pix_transactions
where is_complete_month
group by month_start
order by month_start
