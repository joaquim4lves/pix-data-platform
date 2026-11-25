select
    pagador_regiao_label as payer_region,
    recebedor_regiao_label as receiver_region,
    sum(valor) as settled_value
from marts.fct_pix_transactions
where is_complete_month
    and ano_mes = (select max(ano_mes) from marts.fct_pix_transactions where is_complete_month)
group by 1, 2
order by settled_value desc
