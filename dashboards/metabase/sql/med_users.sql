select month_start, usuarios_com_marcacao as users_with_a_fraud_mark
from marts.fct_pix_med
where is_complete_month and ano_mes >= 202201
order by month_start
