select
    recebedor_lado as receiver,
    sum(case when pagador_lado = 'P' then valor else 0 end) as payer_p,
    sum(case when pagador_lado = 'B' then valor else 0 end) as payer_b,
    sum(case when pagador_lado = 'G' then valor else 0 end) as payer_g
from marts.fct_pix_transactions
where is_complete_month
    and ano_mes = (select max(ano_mes) from marts.fct_pix_transactions where is_complete_month)
    and pagador_lado in ('P', 'B', 'G')
    and recebedor_lado in ('P', 'B', 'G')
group by recebedor_lado
order by case recebedor_lado when 'P' then 1 when 'B' then 2 else 3 end
