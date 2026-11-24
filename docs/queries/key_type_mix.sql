-- Mix of active PIX keys by type on the latest snapshot month.
-- ChavesPix is a stock of keys, not a count or a value of payments.
-- The transaction extracts have no ISPB, so this is not per-bank volume.

with latest as (
    select max(ano_mes) as ano_mes
    from marts.fct_chaves_pix
)
select
    chaves.tipo_chave,
    tipo.rotulo,
    sum(chaves.quantidade_chaves) as quantidade_chaves
from marts.fct_chaves_pix as chaves
inner join latest
    on chaves.ano_mes = latest.ano_mes
inner join marts.dim_tipo_chave as tipo
    on chaves.tipo_chave = tipo.codigo
group by
    chaves.tipo_chave,
    tipo.rotulo
order by quantidade_chaves desc, chaves.tipo_chave
