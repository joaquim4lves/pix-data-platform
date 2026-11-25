select month_start, tipo_chave, sum(quantidade_chaves) as key_stock
from marts.fct_pix_keys_stock
where is_complete_month
[[and {{period}}]]
group by month_start, tipo_chave
order by month_start, tipo_chave
