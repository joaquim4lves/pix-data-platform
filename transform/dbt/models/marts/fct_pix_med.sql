-- National MED month. No geography. Rows start at 202201, which is the
-- first month the spike found. Missing months are absent, not zero.
-- PercentualdeDevolucao and the per-100k rate are stored as published.
-- Precautionary-block measures are not on this mart.

select
    ano_mes,
    {{ month_start('ano_mes') }} as month_start,
    {{ is_complete_month('ano_mes') }} as is_complete_month,
    cast(quantidade_contestada as bigint) as quantidade_contestada,
    cast(quantidade_aceita as bigint) as quantidade_aceita,
    cast(quantidade_rejeitada as bigint) as quantidade_rejeitada,
    aceitas_por_100mil,
    cast(usuarios_com_marcacao as bigint) as usuarios_com_marcacao,
    cast(chaves_com_marcacao as bigint) as chaves_com_marcacao,
    valor_aceito,
    cast(quantidade_devolvida_integral as bigint) as quantidade_devolvida_integral,
    valor_devolvido_integral,
    cast(quantidade_devolvida_parcial as bigint) as quantidade_devolvida_parcial,
    valor_devolvido_parcial,
    cast(quantidade_nao_devolvida_saldo as bigint) as quantidade_nao_devolvida_saldo,
    valor_nao_devolvido_saldo,
    cast(quantidade_nao_devolvida_conta as bigint) as quantidade_nao_devolvida_conta,
    valor_nao_devolvido_conta,
    cast(quantidade_nao_devolvida_outros as bigint) as quantidade_nao_devolvida_outros,
    valor_nao_devolvido_outros,
    percentual_devolucao
from {{ ref('stg_estatisticas_fraudes_pix') }}
where ano_mes >= 202201
