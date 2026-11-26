-- Month-end stock of PIX keys. Not a count of users and not payment volume.
-- Grain: ano_mes, ispb, natureza_usuario, tipo_chave. nome and segmento
-- are the values published on that snapshot, not the type-1 current name.

select
    ano_mes,
    {{ month_start('ano_mes') }} as month_start,
    {{ is_complete_month('ano_mes') }} as is_complete_month,
    data_referencia,
    ispb,
    nome,
    segmento,
    natureza_usuario,
    tipo_chave,
    quantidade_chaves
from {{ ref('int_chaves_pix') }}
