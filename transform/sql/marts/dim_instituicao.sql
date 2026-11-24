-- One row per ISPB. Type 1: nome and segmento come from the latest
-- snapshot month, so a rename does not keep history. The fact still has
-- one row per month. ChavesPix is a stock of keys by institution, not
-- payment volume. The transaction extracts have no ISPB.
-- Grain: ispb.

with ranked as (
    select
        ispb,
        nome,
        segmento,
        ano_mes,
        row_number() over (
            partition by ispb
            order by ano_mes desc, data_referencia desc
        ) as rn
    from intermediate.int_chaves_pix
)
select
    ispb,
    nome,
    segmento,
    ano_mes as ano_mes_referencia
from ranked
where rn = 1
