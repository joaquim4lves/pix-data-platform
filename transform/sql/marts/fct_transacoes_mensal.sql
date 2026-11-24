-- Monthly PIX transactions settled in SPI, at the published grain.
-- Grain: ano_mes, pagador_tipo_pessoa, recebedor_tipo_pessoa,
-- pagador_regiao, recebedor_regiao, pagador_faixa_idade,
-- recebedor_faixa_idade, forma_iniciacao, natureza, finalidade.
-- valor and quantidade add across this grain to the national total for
-- the month. Payer and receiver are columns of the same row, so summing
-- valor does not double-count. There is no ISPB and no day. Banco Central
-- do Brasil describes this resource as quantity and value settled in the
-- month, excluding PIX settled on the participant's own books (not sent
-- to SPI). The payload has no column for that exclusion.

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
from intermediate.int_transacoes_mensal
