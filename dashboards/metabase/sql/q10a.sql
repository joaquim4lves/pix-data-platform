select
    month_start,
    quantidade_contestada as contested_via_med,
    quantidade_aceita as accepted,
    percentual_devolucao as percentual_de_devolucao
from marts.fct_pix_med
where is_complete_month
    and ano_mes >= 202201
[[and {{med_period}}]]
order by month_start
