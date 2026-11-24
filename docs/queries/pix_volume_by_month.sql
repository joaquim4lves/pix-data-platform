-- PIX value and transaction count by month.
-- Summing fct_transacoes_mensal across its grain is the national total
-- for that month. Payer and receiver sit on the same row, so the sum
-- does not double-count.

select
    tempo.ano_mes,
    sum(fct.valor) as valor,
    sum(fct.quantidade) as quantidade
from marts.fct_transacoes_mensal as fct
inner join marts.dim_tempo as tempo
    on fct.ano_mes = tempo.ano_mes
group by tempo.ano_mes
order by tempo.ano_mes
