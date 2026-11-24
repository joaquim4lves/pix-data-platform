-- Grain: one row per snapshot month, ISPB, user nature, and key type.

select
    ano_mes,
    ispb,
    natureza_usuario,
    tipo_chave,
    count(*) as rows
from {{ ref('fct_chaves_pix') }}
group by
    ano_mes,
    ispb,
    natureza_usuario,
    tipo_chave
having count(*) > 1
