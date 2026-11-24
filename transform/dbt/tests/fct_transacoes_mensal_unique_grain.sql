-- Grain: month x payer/receiver person type, region, and age band x
-- initiation form x natureza x finalidade.

select
    ano_mes,
    pagador_tipo_pessoa,
    recebedor_tipo_pessoa,
    pagador_regiao,
    recebedor_regiao,
    pagador_faixa_idade,
    recebedor_faixa_idade,
    forma_iniciacao,
    natureza,
    finalidade,
    count(*) as rows
from {{ ref('fct_transacoes_mensal') }}
group by
    ano_mes,
    pagador_tipo_pessoa,
    recebedor_tipo_pessoa,
    pagador_regiao,
    recebedor_regiao,
    pagador_faixa_idade,
    recebedor_faixa_idade,
    forma_iniciacao,
    natureza,
    finalidade
having count(*) > 1
