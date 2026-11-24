select
    ano_mes,
    ispb,
    tipo_chave,
    quantidade_chaves
from {{ ref('fct_chaves_pix') }}
where quantidade_chaves < 0
