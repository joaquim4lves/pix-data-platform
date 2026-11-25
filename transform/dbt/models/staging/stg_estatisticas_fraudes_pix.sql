-- Typed EstatisticasFraudesPix. One national row per published AnoMes.
-- Quantities stay decimal at this layer because Olinda types them as
-- Edm.Decimal. The mart casts the counts. Precautionary-block columns
-- are kept here and are not selected by the v1.0 mart.

select
    cast("AnoMes" as integer) as ano_mes,
    cast("QtdePixcontestados" as decimal(38, 8)) as quantidade_contestada,
    cast("Qtdecontestacoesaceitas" as decimal(38, 8)) as quantidade_aceita,
    cast("Qtdecontestacoesrejeitadas" as decimal(38, 8)) as quantidade_rejeitada,
    cast("Qtdecontestacoesaceitasacada100mil" as decimal(38, 8)) as aceitas_por_100mil,
    cast("QtdeUsuarioscommarcacoesdefraude" as decimal(38, 8)) as usuarios_com_marcacao,
    cast("QtdeChavesPixcommarcacoesdefraude" as decimal(38, 8)) as chaves_com_marcacao,
    cast("ValorPixcontestadosaceitos" as decimal(38, 8)) as valor_aceito,
    cast("QuantidadedevolvidaintegralmentepormeiodoMED" as decimal(38, 8))
        as quantidade_devolvida_integral,
    cast("ValorPixdevolvidosintegralmente" as decimal(38, 8)) as valor_devolvido_integral,
    cast("QuantidadedevolvidaparcialmentepormeiodoMED" as decimal(38, 8))
        as quantidade_devolvida_parcial,
    cast("ValorPixdevolvidosparcialmente" as decimal(38, 8)) as valor_devolvido_parcial,
    cast("Quantidadedenaodevolvidossaldoinsuficiente" as decimal(38, 8))
        as quantidade_nao_devolvida_saldo,
    cast("ValorPixnaodevolvidossaldoinsuficiente" as decimal(38, 8)) as valor_nao_devolvido_saldo,
    cast("Quantidadedenaodevolvidoscontaencerrada" as decimal(38, 8))
        as quantidade_nao_devolvida_conta,
    cast("Valornaodevolvidoscontaencerrada" as decimal(38, 8)) as valor_nao_devolvido_conta,
    cast("Quantidadedenaodevolvidosmotivosdiversos" as decimal(38, 8))
        as quantidade_nao_devolvida_outros,
    cast("ValorPixnaodevolvidosmotivosdiversos" as decimal(38, 8)) as valor_nao_devolvido_outros,
    cast("PercentualdeDevolucao" as decimal(38, 8)) as percentual_devolucao
from {{ source('raw', 'estatisticas_fraudes_pix') }}
where "AnoMes" is not null
