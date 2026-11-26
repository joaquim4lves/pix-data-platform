-- Settled value and payments received, by person type, CNAE section,
-- porte and MEI. mesmatit, formainic, finalidade and natureza are
-- summed away: they are not on the v1.0 dashboards, and neither are
-- vlcompra or vldinespec. Average ticket is valor_liquidado /
-- quantidade_liquidada at whatever grain the question groups to.
-- 'Pessoa fisica' and 'Outros' stay as their own CNAE section labels.
-- MEI keeps Outros as published. Porte still folds a residual Outros.

with summed as (
    select
        ano_mes,
        tipo_pessoa,
        porte,
        mei,
        cnae_secao,
        sum(valor_liquidado) as valor_liquidado,
        sum(quantidade_liquidada) as quantidade_liquidada
    from {{ ref('stg_cnae_porte_recebedor') }}
    group by ano_mes, tipo_pessoa, porte, mei, cnae_secao
)
select
    ano_mes,
    {{ month_start('ano_mes') }} as month_start,
    {{ is_complete_month('ano_mes') }} as is_complete_month,
    tipo_pessoa,
    porte as porte_raw,
    {{ label_with_token('porte', true) }} as porte_label,
    mei as mei_raw,
    {{ label_with_token('mei', false) }} as mei_label,
    cnae_secao as cnae_secao_raw,
    {{ label_with_token('cnae_secao', false) }} as cnae_secao_label,
    valor_liquidado,
    quantidade_liquidada
from summed
