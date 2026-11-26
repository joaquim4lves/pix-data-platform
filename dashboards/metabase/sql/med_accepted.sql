select
    month_start as reference_month,
    quantidade_aceita as accepted,
    aceitas_por_100mil as per_100k_as_published
from marts.fct_pix_med
where ano_mes = (select max(ano_mes) from marts.fct_pix_med where is_complete_month)
