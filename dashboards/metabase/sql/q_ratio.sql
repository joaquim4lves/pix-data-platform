select month_start, ratio_aceito_sobre_spi as accepted_value_over_spi
from marts.fct_pix_med_vs_spi
where is_complete_month
    and ano_mes >= 202201
[[and {{med_period}}]]
order by month_start
