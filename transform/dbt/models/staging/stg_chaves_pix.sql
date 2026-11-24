-- Typed, renamed projection of ChavesPix.
-- ISPB stays text so leading zeros survive. The month key is derived
-- from the snapshot date in intermediate.

select
    cast("Data" as date) as data_referencia,
    trim("ISPB") as ispb,
    trim("Nome") as nome,
    trim("NaturezaUsuario") as natureza_usuario,
    trim("TipoChave") as tipo_chave,
    cast("qtdChaves" as bigint) as quantidade_chaves,
    trim("Segmento") as segmento
from {{ source('raw', 'chaves_pix') }}
