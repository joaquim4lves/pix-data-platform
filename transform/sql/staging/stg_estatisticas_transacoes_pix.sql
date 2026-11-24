-- Typed, renamed projection of EstatisticasTransacoesPix.
-- Quoted identifiers are the physical Olinda names. Every later model
-- uses the snake_case columns. Measures stay DECIMAL(38, 8), the scale
-- the raw writer stores.

select
    cast("AnoMes" as integer) as ano_mes,
    trim("PAG_PFPJ") as pagador_tipo_pessoa,
    trim("REC_PFPJ") as recebedor_tipo_pessoa,
    trim("PAG_REGIAO") as pagador_regiao,
    trim("REC_REGIAO") as recebedor_regiao,
    trim("PAG_IDADE") as pagador_faixa_idade,
    trim("REC_IDADE") as recebedor_faixa_idade,
    trim("FORMAINICIACAO") as forma_iniciacao,
    trim("NATUREZA") as natureza,
    trim("FINALIDADE") as finalidade,
    cast("VALOR" as decimal(38, 8)) as valor,
    cast("QUANTIDADE" as decimal(38, 8)) as quantidade
from raw.estatisticas_transacoes_pix
