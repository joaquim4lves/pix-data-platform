-- Municipalities ranked by PIX value received.
-- Not per capita: PIX open data does not include population, so this
-- ranking is the raw value only.
-- municipio_ibge 0 ("Não informado", the published N/D row) is excluded
-- so the unassigned bucket cannot take first place.

select
    municipio.nome,
    municipio.uf_sigla,
    sum(fct.valor_recebido) as valor_recebido,
    sum(fct.quantidade_recebida) as quantidade_recebida
from marts.fct_transacoes_municipio as fct
inner join marts.dim_municipio as municipio
    on fct.municipio_ibge = municipio.municipio_ibge
where municipio.municipio_ibge <> 0
group by
    municipio.nome,
    municipio.uf_sigla,
    municipio.municipio_ibge
order by valor_recebido desc, municipio.nome
