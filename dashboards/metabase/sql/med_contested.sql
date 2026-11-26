select month_start, quantidade_contestada as contested_via_med
from marts.fct_pix_med
where is_complete_month and ano_mes >= 202201
order by month_start
