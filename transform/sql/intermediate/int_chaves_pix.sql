-- Key stock for one snapshot month.
-- ChavesPix dates in the extract are the last calendar day of the month.
-- ano_mes is that month. ISPB is left-padded to 8 characters; a value
-- that is already 8 characters is unchanged, including leading zeros.

select
    data_referencia,
    cast(substr(cast(data_referencia as varchar), 1, 4) as integer) * 100
        + cast(substr(cast(data_referencia as varchar), 6, 2) as integer) as ano_mes,
    lpad(ispb, 8, '0') as ispb,
    nome,
    natureza_usuario,
    tipo_chave,
    quantidade_chaves,
    segmento
from staging.stg_chaves_pix
