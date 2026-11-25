-- Dashboard grain of SPI-settled PIX. Same grain as fct_transacoes_mensal,
-- plus chart labels. valor and quantidade still add to the national month.
-- Payer and receiver stay on the same row. Do not add them.
-- AUTO, APDN and APES keep the code only. Residual tokens stay visible
-- as 'Unstated / other (<raw>)'.

select
    ano_mes,
    {{ month_start('ano_mes') }} as month_start,
    {{ is_complete_month('ano_mes') }} as is_complete_month,
    pagador_tipo_pessoa,
    recebedor_tipo_pessoa,
    pagador_regiao as pagador_regiao_raw,
    {{ label_with_token('pagador_regiao') }} as pagador_regiao_label,
    recebedor_regiao as recebedor_regiao_raw,
    {{ label_with_token('recebedor_regiao') }} as recebedor_regiao_label,
    pagador_faixa_idade as pagador_idade_raw,
    {{ label_with_token('pagador_faixa_idade') }} as pagador_idade_label,
    recebedor_faixa_idade as recebedor_idade_raw,
    {{ label_with_token('recebedor_faixa_idade') }} as recebedor_idade_label,
    forma_iniciacao as forma_iniciacao_raw,
    case trim(forma_iniciacao)
        when 'DICT' then 'DICT · Pix key'
        when 'QRDN' then 'QRDN · dynamic QR'
        when 'QRES' then 'QRES · static QR'
        when 'MANU' then 'MANU · manual details'
        when 'INIC' then 'INIC · payment initiator'
        when 'AUTO' then 'AUTO'
        when 'APDN' then 'APDN'
        when 'APES' then 'APES'
        when 'Nao disponivel' then 'Unstated / other (Nao disponivel)'
        else {{ label_with_token('forma_iniciacao') }}
    end as forma_iniciacao_label,
    natureza,
    case
        when natureza in ('P2P', 'P2B', 'P2G') then 'P'
        when natureza in ('B2P', 'B2B', 'B2G') then 'B'
        when natureza in ('G2P', 'G2B', 'G2G') then 'G'
        else substr(natureza, 1, 1)
    end as pagador_lado,
    case
        when natureza in ('P2P', 'B2P', 'G2P') then 'P'
        when natureza in ('P2B', 'B2B', 'G2B') then 'B'
        when natureza in ('P2G', 'B2G', 'G2G') then 'G'
        else substr(natureza, 3, 1)
    end as recebedor_lado,
    finalidade as finalidade_raw,
    case trim(finalidade)
        when 'Nao disponivel' then 'Unstated / other (Nao disponivel)'
        else {{ label_with_token('finalidade') }}
    end as finalidade_label,
    valor,
    quantidade
from {{ ref('fct_transacoes_mensal') }}
