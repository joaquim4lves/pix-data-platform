select
    ano_mes,
    pagador_tipo_pessoa,
    recebedor_tipo_pessoa,
    pagador_regiao_raw,
    recebedor_regiao_raw,
    pagador_idade_raw,
    recebedor_idade_raw,
    forma_iniciacao_raw,
    natureza,
    finalidade_raw,
    count(*) as rows
from {{ ref('fct_pix_transactions') }}
group by
    ano_mes,
    pagador_tipo_pessoa,
    recebedor_tipo_pessoa,
    pagador_regiao_raw,
    recebedor_regiao_raw,
    pagador_idade_raw,
    recebedor_idade_raw,
    forma_iniciacao_raw,
    natureza,
    finalidade_raw
having count(*) > 1
