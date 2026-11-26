select
    month_start,
    sum(valor) / nullif(sum(quantidade), 0) as average_ticket
from marts.fct_pix_transactions
where is_complete_month
group by month_start
order by month_start
