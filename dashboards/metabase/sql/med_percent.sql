select month_start, percentual_devolucao as percentual_de_devolucao
from marts.fct_pix_med
where is_complete_month and ano_mes >= 202201
order by month_start
