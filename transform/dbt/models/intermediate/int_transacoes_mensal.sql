-- Conformed monthly transaction grain.
-- One row for each raw combination of month, payer and receiver person
-- type, region, age band, initiation form, natureza, and finalidade.
-- Nothing is filtered: a new code stays on the row and is picked up by
-- the matching dimension.

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
    valor,
    quantidade
from {{ ref('stg_estatisticas_transacoes_pix') }}
