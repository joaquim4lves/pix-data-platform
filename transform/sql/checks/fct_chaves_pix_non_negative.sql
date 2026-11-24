select
    ano_mes,
    ispb,
    tipo_chave,
    quantidade_chaves
from marts.fct_chaves_pix
where quantidade_chaves < 0
