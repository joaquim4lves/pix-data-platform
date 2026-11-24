-- The latest snapshot for an ISPB must carry one name and one segment.
-- The type-1 dimension would otherwise hide a clash.

with latest as (
    select
        ispb,
        max(ano_mes) as ano_mes
    from {{ ref('int_chaves_pix') }}
    group by ispb
)
select
    chaves.ispb,
    count(distinct chaves.nome) as nomes,
    count(distinct chaves.segmento) as segmentos
from {{ ref('int_chaves_pix') }} as chaves
inner join latest
    on chaves.ispb = latest.ispb
    and chaves.ano_mes = latest.ano_mes
group by chaves.ispb
having count(distinct chaves.nome) > 1
    or count(distinct chaves.segmento) > 1
