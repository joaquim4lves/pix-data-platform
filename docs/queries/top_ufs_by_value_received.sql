-- UFs ranked by PIX value received (recebedor PF + PJ).
-- This is not per capita. The raw zone has no population.
-- uf_ibge 0 is the "Não informado" bucket and is left out of the ranking.
-- Value sent and value received are two sides of the same payments.
-- This query uses value received and does not add the two sides.

select
    municipio.uf_sigla,
    municipio.uf_nome,
    sum(fct.valor_recebido) as valor_recebido,
    sum(fct.quantidade_recebida) as quantidade_recebida
from marts.fct_transacoes_municipio as fct
inner join marts.dim_municipio as municipio
    on fct.municipio_ibge = municipio.municipio_ibge
where municipio.uf_ibge <> 0
group by
    municipio.uf_sigla,
    municipio.uf_nome
order by valor_recebido desc, municipio.uf_sigla
