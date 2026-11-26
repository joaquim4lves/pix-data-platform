select nome, segmento, sum(quantidade_chaves) as key_stock
from marts.fct_pix_keys_stock
where ano_mes = (select max(ano_mes) from marts.fct_pix_keys_stock where is_complete_month)
group by nome, segmento
order by key_stock desc
limit 10
