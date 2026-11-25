"""Write dashboards/metabase SQL and collection.json. Run from the repo root."""

# SQL and question copy are kept on one line so the generated files stay readable.
# ruff: noqa: E501

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "metabase"
FOOTER = (
    "Source: Banco Central do Brasil, Estatísticas do Pix. Transaction figures are "
    "SPI-settled only and exclude Pix settled on the participant's own books."
)
RATIO_CAPTION = (
    "Approximate ratio computed by this portfolio; denominator is SPI-only (no on-us). "
    "Not an official BCB rate."
)

SQL: dict[str, str] = {}

SQL["q1_tx_count"] = """
select month_start, cast(round(sum(quantidade)) as bigint) as transactions
from marts.fct_pix_transactions
where is_complete_month
group by month_start
order by month_start
"""

SQL["q1_tx_value"] = """
select month_start, sum(valor) as settled_value
from marts.fct_pix_transactions
where is_complete_month
group by month_start
order by month_start
"""

SQL["q1_ticket"] = """
select
    month_start,
    sum(valor) / nullif(sum(quantidade), 0) as average_ticket
from marts.fct_pix_transactions
where is_complete_month
group by month_start
order by month_start
"""

SQL["q1_dict_users"] = """
select
    month_start as reference_month,
    usuarios_total as dict_users,
    usuarios_pf as pessoa_fisica,
    usuarios_pj as pessoa_juridica
from marts.fct_pix_dict_users
where is_complete_month
order by month_start desc
limit 1
"""

SQL["q2_trend"] = """
select
    month_start,
    sum(valor) as settled_value,
    cast(round(sum(quantidade)) as bigint) as transactions
from marts.fct_pix_transactions
where is_complete_month
[[and {{period}}]]
group by month_start
order by month_start
"""

SQL["q3_natureza"] = """
select
    month_start,
    natureza,
    case
        when {{measure}} = 'count' then sum(quantidade)
        else sum(valor)
    end as amount
from marts.fct_pix_transactions
where is_complete_month
[[and {{period}}]]
group by month_start, natureza
order by month_start, natureza
"""

SQL["q3_matrix"] = """
select
    recebedor_lado as receiver,
    sum(case when pagador_lado = 'P' then valor else 0 end) as payer_p,
    sum(case when pagador_lado = 'B' then valor else 0 end) as payer_b,
    sum(case when pagador_lado = 'G' then valor else 0 end) as payer_g
from marts.fct_pix_transactions
where is_complete_month
    and ano_mes = (select max(ano_mes) from marts.fct_pix_transactions where is_complete_month)
    and pagador_lado in ('P', 'B', 'G')
    and recebedor_lado in ('P', 'B', 'G')
group by recebedor_lado
order by case recebedor_lado when 'P' then 1 when 'B' then 2 else 3 end
"""

SQL["q4_iniciacao"] = """
select month_start, forma_iniciacao_label, forma_iniciacao_raw, sum(valor) as settled_value
from marts.fct_pix_transactions
where is_complete_month
[[and {{period}}]]
group by month_start, forma_iniciacao_label, forma_iniciacao_raw
order by month_start, forma_iniciacao_label
"""

SQL["q4_finalidade"] = """
select
    finalidade_label,
    finalidade_raw,
    sum(valor) as settled_value,
    cast(round(sum(quantidade)) as bigint) as transactions
from marts.fct_pix_transactions
where is_complete_month
[[and {{period}}]]
group by finalidade_label, finalidade_raw
order by settled_value desc
"""

SQL["q5_users"] = """
select month_start, usuarios_total, usuarios_pf as pessoa_fisica, usuarios_pj as pessoa_juridica
from marts.fct_pix_dict_users
where is_complete_month
[[and {{period}}]]
order by month_start
"""

SQL["q5_keys"] = """
select month_start, tipo_chave, sum(quantidade_chaves) as key_stock
from marts.fct_pix_keys_stock
where is_complete_month
[[and {{period}}]]
group by month_start, tipo_chave
order by month_start, tipo_chave
"""

SQL["q5_participants"] = """
select nome, segmento, sum(quantidade_chaves) as key_stock
from marts.fct_pix_keys_stock
where ano_mes = (select max(ano_mes) from marts.fct_pix_keys_stock where is_complete_month)
group by nome, segmento
order by key_stock desc
limit 10
"""

SQL["q6_kpi_value"] = """
select sum(
    case
        when {{person}} = 'PF' and {{view}} = 'payer' then valor_pagador_pf
        when {{person}} = 'PJ' and {{view}} = 'payer' then valor_pagador_pj
        when {{view}} = 'payer' then valor_pagador
        when {{person}} = 'PF' then valor_recebedor_pf
        when {{person}} = 'PJ' then valor_recebedor_pj
        else valor_recebedor
    end
) as settled_value
from marts.fct_pix_municipality
where is_complete_month
[[and {{period}}]]
and ({{region}} = 'All' or regiao_label = {{region}})
and ({{state}} = 'All' or state_label = {{state}})
and ({{municipality}} = '' or lower(municipio_label) like '%' || lower({{municipality}}) || '%')
"""

SQL["q6_kpi_payments"] = """
select cast(round(sum(
    case
        when {{person}} = 'PF' and {{view}} = 'payer' then quantidade_pagador_pf
        when {{person}} = 'PJ' and {{view}} = 'payer' then quantidade_pagador_pj
        when {{view}} = 'payer' then quantidade_pagador
        when {{person}} = 'PF' then quantidade_recebedor_pf
        when {{person}} = 'PJ' then quantidade_recebedor_pj
        else quantidade_recebedor
    end
)) as bigint) as payments
from marts.fct_pix_municipality
where is_complete_month
[[and {{period}}]]
and ({{region}} = 'All' or regiao_label = {{region}})
and ({{state}} = 'All' or state_label = {{state}})
and ({{municipality}} = '' or lower(municipio_label) like '%' || lower({{municipality}}) || '%')
"""

SQL["q6_kpi_people"] = """
with filtered as (
    select
        municipio_ibge,
        sum(
            case
                when {{person}} = 'PF' and {{view}} = 'payer' then pessoas_pagador_pf
                when {{person}} = 'PJ' and {{view}} = 'payer' then pessoas_pagador_pj
                when {{view}} = 'payer' then pessoas_pagador
                when {{person}} = 'PF' then pessoas_recebedor_pf
                when {{person}} = 'PJ' then pessoas_recebedor_pj
                else pessoas_recebedor
            end
        ) as pessoas
    from marts.fct_pix_municipality
    where is_complete_month
    [[and {{period}}]]
    and ({{region}} = 'All' or regiao_label = {{region}})
    and ({{state}} = 'All' or state_label = {{state}})
    and ({{municipality}} = '' or lower(municipio_label) like '%' || lower({{municipality}}) || '%')
    group by municipio_ibge
)
select cast(round(sum(pessoas)) as bigint) as distinct_people
from filtered
having count(*) = 1
"""

SQL["q6_region"] = """
select
    regiao_label,
    regiao_raw,
    sum(
        case
            when {{person}} = 'PF' and {{view}} = 'payer' then valor_pagador_pf
            when {{person}} = 'PJ' and {{view}} = 'payer' then valor_pagador_pj
            when {{view}} = 'payer' then valor_pagador
            when {{person}} = 'PF' then valor_recebedor_pf
            when {{person}} = 'PJ' then valor_recebedor_pj
            else valor_recebedor
        end
    ) as settled_value
from marts.fct_pix_municipality
where is_complete_month
[[and {{period}}]]
and ({{state}} = 'All' or state_label = {{state}})
and ({{municipality}} = '' or lower(municipio_label) like '%' || lower({{municipality}}) || '%')
group by regiao_label, regiao_raw
order by settled_value desc
"""

SQL["q6_state"] = """
select
    state_label,
    uf_raw,
    sum(
        case
            when {{person}} = 'PF' and {{view}} = 'payer' then valor_pagador_pf
            when {{person}} = 'PJ' and {{view}} = 'payer' then valor_pagador_pj
            when {{view}} = 'payer' then valor_pagador
            when {{person}} = 'PF' then valor_recebedor_pf
            when {{person}} = 'PJ' then valor_recebedor_pj
            else valor_recebedor
        end
    ) as settled_value
from marts.fct_pix_municipality
where is_complete_month
[[and {{period}}]]
and ({{region}} = 'All' or regiao_label = {{region}})
and ({{municipality}} = '' or lower(municipio_label) like '%' || lower({{municipality}}) || '%')
group by state_label, uf_raw
order by settled_value desc
"""

SQL["q6_table"] = """
with filtered as (
    select *
    from marts.fct_pix_municipality
    where is_complete_month
    [[and {{period}}]]
    and ({{region}} = 'All' or regiao_label = {{region}})
    and ({{state}} = 'All' or state_label = {{state}})
    and ({{municipality}} = '' or lower(municipio_label) like '%' || lower({{municipality}}) || '%')
),
rolled as (
    select
        municipio_label,
        municipio_raw,
        state_label,
        regiao_label,
        sum(
            case
                when {{person}} = 'PF' and {{view}} = 'payer' then valor_pagador_pf
                when {{person}} = 'PJ' and {{view}} = 'payer' then valor_pagador_pj
                when {{view}} = 'payer' then valor_pagador
                when {{person}} = 'PF' then valor_recebedor_pf
                when {{person}} = 'PJ' then valor_recebedor_pj
                else valor_recebedor
            end
        ) as settled_value,
        cast(round(sum(
            case
                when {{person}} = 'PF' and {{view}} = 'payer' then quantidade_pagador_pf
                when {{person}} = 'PJ' and {{view}} = 'payer' then quantidade_pagador_pj
                when {{view}} = 'payer' then quantidade_pagador
                when {{person}} = 'PF' then quantidade_recebedor_pf
                when {{person}} = 'PJ' then quantidade_recebedor_pj
                else quantidade_recebedor
            end
        )) as bigint) as payments,
        sum(case when {{view}} = 'payer' then valor_pagador_pf else valor_recebedor_pf end) as pessoa_fisica_value,
        sum(case when {{view}} = 'payer' then valor_pagador_pj else valor_recebedor_pj end) as pessoa_juridica_value,
        sum(
            case
                when {{person}} = 'PF' and {{view}} = 'payer' then pessoas_pagador_pf
                when {{person}} = 'PJ' and {{view}} = 'payer' then pessoas_pagador_pj
                when {{view}} = 'payer' then pessoas_pagador
                when {{person}} = 'PF' then pessoas_recebedor_pf
                when {{person}} = 'PJ' then pessoas_recebedor_pj
                else pessoas_recebedor
            end
        ) as distinct_people_row
    from filtered
    group by municipio_label, municipio_raw, state_label, regiao_label
)
select
    municipio_label as municipality,
    municipio_raw,
    state_label as state,
    regiao_label as region,
    settled_value,
    payments,
    pessoa_fisica_value,
    pessoa_juridica_value,
    case when count(*) over () = 1 then distinct_people_row else null end as distinct_people
from rolled
order by settled_value desc
"""

SQL["q6_top"] = """
select
    municipio_label as municipality,
    sum(
        case
            when {{person}} = 'PF' and {{view}} = 'payer' then valor_pagador_pf
            when {{person}} = 'PJ' and {{view}} = 'payer' then valor_pagador_pj
            when {{view}} = 'payer' then valor_pagador
            when {{person}} = 'PF' then valor_recebedor_pf
            when {{person}} = 'PJ' then valor_recebedor_pj
            else valor_recebedor
        end
    ) as settled_value
from marts.fct_pix_municipality
where is_complete_month
[[and {{period}}]]
and ({{region}} = 'All' or regiao_label = {{region}})
and ({{state}} = 'All' or state_label = {{state}})
and ({{municipality}} = '' or lower(municipio_label) like '%' || lower({{municipality}}) || '%')
group by municipio_label
order by settled_value desc
limit 20
"""

SQL["q8_age"] = """
select
    case when {{view}} = 'payer' then pagador_idade_label else recebedor_idade_label end as age_band,
    case when {{view}} = 'payer' then pagador_idade_raw else recebedor_idade_raw end as raw_token,
    cast(round(sum(quantidade)) as bigint) as transactions
from marts.fct_pix_transactions
where is_complete_month
    and {{state}} = 'All'
    and {{municipality}} = ''
    and ({{region}} = 'All' or (
        ({{view}} = 'payer' and pagador_regiao_label = {{region}})
        or ({{view}} <> 'payer' and recebedor_regiao_label = {{region}})
    ))
    and (
        ({{view}} = 'payer' and pagador_tipo_pessoa = 'PF' and pagador_idade_raw <> 'Nao se aplica')
        or ({{view}} <> 'payer' and recebedor_tipo_pessoa = 'PF' and recebedor_idade_raw <> 'Nao se aplica')
    )
[[and {{period}}]]
group by 1, 2
order by transactions desc
"""

SQL["q8_notice"] = """
select
    'Age is national only. Clear the state and municipality filters. This series has no municipality grain.' as notice
from (select 1) as _
where {{state}} <> 'All' or {{municipality}} <> ''
"""

SQL["q7_flow"] = """
select
    pagador_regiao_label as payer_region,
    recebedor_regiao_label as receiver_region,
    sum(valor) as settled_value
from marts.fct_pix_transactions
where is_complete_month
    and ano_mes = (select max(ano_mes) from marts.fct_pix_transactions where is_complete_month)
group by 1, 2
order by settled_value desc
"""

SQL["q9_kpi_value"] = """
select sum(valor_liquidado) as settled_value
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{porte}} = 'All' or porte_label = {{porte}})
and ({{section}} = 'All' or cnae_secao_label = {{section}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
and ({{mei}} = 'All' or mei_label = {{mei}})
"""

SQL["q9_kpi_payments"] = """
select cast(round(sum(quantidade_liquidada)) as bigint) as payments
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{porte}} = 'All' or porte_label = {{porte}})
and ({{section}} = 'All' or cnae_secao_label = {{section}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
and ({{mei}} = 'All' or mei_label = {{mei}})
"""

SQL["q9_kpi_share"] = """
select
    sum(case when porte_raw in ('Microempresa', 'Pequeno Porte') then valor_liquidado else 0 end)
        / nullif(sum(valor_liquidado), 0) as micro_and_small_share
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{section}} = 'All' or cnae_secao_label = {{section}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
and ({{mei}} = 'All' or mei_label = {{mei}})
"""

SQL["q9_section"] = """
select cnae_secao_label as cnae_section, cnae_secao_raw, sum(valor_liquidado) as settled_value
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{porte}} = 'All' or porte_label = {{porte}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
and ({{mei}} = 'All' or mei_label = {{mei}})
group by cnae_secao_label, cnae_secao_raw
order by settled_value desc
"""

SQL["q9_porte"] = """
select month_start, porte_label, porte_raw, sum(valor_liquidado) as settled_value
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{section}} = 'All' or cnae_secao_label = {{section}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
and ({{mei}} = 'All' or mei_label = {{mei}})
group by month_start, porte_label, porte_raw
order by month_start, porte_label
"""

SQL["q9_mei"] = """
select mei_label, mei_raw, sum(valor_liquidado) as settled_value
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{porte}} = 'All' or porte_label = {{porte}})
and ({{section}} = 'All' or cnae_secao_label = {{section}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
group by mei_label, mei_raw
order by settled_value desc
"""

SQL["q9_ticket_section"] = """
select
    cnae_secao_label as cnae_section,
    sum(valor_liquidado) / nullif(sum(quantidade_liquidada), 0) as average_ticket
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{porte}} = 'All' or porte_label = {{porte}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
and ({{mei}} = 'All' or mei_label = {{mei}})
group by cnae_secao_label
order by average_ticket desc
"""

SQL["q9_ticket_porte"] = """
select
    porte_label,
    sum(valor_liquidado) / nullif(sum(quantidade_liquidada), 0) as average_ticket
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{section}} = 'All' or cnae_secao_label = {{section}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
and ({{mei}} = 'All' or mei_label = {{mei}})
group by porte_label
order by average_ticket desc
"""

SQL["med_banner"] = """
select banner from marts.fct_pix_publication
"""

SQL["med_gap"] = """
select gap_note
from marts.fct_pix_publication
where gap_note is not null
"""

SQL["med_contested"] = """
select month_start, quantidade_contestada as contested_via_med
from marts.fct_pix_med
where is_complete_month and ano_mes >= 202201
order by month_start
"""

SQL["med_accepted"] = """
select
    month_start as reference_month,
    quantidade_aceita as accepted,
    aceitas_por_100mil as per_100k_as_published
from marts.fct_pix_med
where ano_mes = (select max(ano_mes) from marts.fct_pix_med where is_complete_month)
"""

SQL["med_percent"] = """
select month_start, percentual_devolucao as percentual_de_devolucao
from marts.fct_pix_med
where is_complete_month and ano_mes >= 202201
order by month_start
"""

SQL["med_users"] = """
select month_start, usuarios_com_marcacao as users_with_a_fraud_mark
from marts.fct_pix_med
where is_complete_month and ano_mes >= 202201
order by month_start
"""

SQL["med_keys"] = """
select month_start, chaves_com_marcacao as keys_with_a_fraud_mark
from marts.fct_pix_med
where is_complete_month and ano_mes >= 202201
order by month_start
"""

SQL["q10a"] = """
select
    month_start,
    quantidade_contestada as contested_via_med,
    quantidade_aceita as accepted,
    percentual_devolucao as percentual_de_devolucao
from marts.fct_pix_med
where is_complete_month
    and ano_mes >= 202201
[[and {{med_period}}]]
order by month_start
"""

SQL["q_ratio"] = """
select month_start, ratio_aceito_sobre_spi as accepted_value_over_spi
from marts.fct_pix_med_vs_spi
where is_complete_month
    and ano_mes >= 202201
[[and {{med_period}}]]
order by month_start
"""

SQL["q10b"] = """
with latest as (
    select *
    from marts.fct_pix_med
    where ano_mes = (select max(ano_mes) from marts.fct_pix_med where is_complete_month)
)
select 'Insufficient balance' as category, 'reason' as kind,
    case when {{med_measure}} = 'count' then quantidade_nao_devolvida_saldo else valor_nao_devolvido_saldo end as amount
from latest
union all
select 'Account closed', 'reason',
    case when {{med_measure}} = 'count' then quantidade_nao_devolvida_conta else valor_nao_devolvido_conta end
from latest
union all
select 'Other', 'reason',
    case when {{med_measure}} = 'count' then quantidade_nao_devolvida_outros else valor_nao_devolvido_outros end
from latest
union all
select 'Full return (comparison)', 'comparison',
    case when {{med_measure}} = 'count' then quantidade_devolvida_integral else valor_devolvido_integral end
from latest
union all
select 'Partial return (comparison)', 'comparison',
    case when {{med_measure}} = 'count' then quantidade_devolvida_parcial else valor_devolvido_parcial end
from latest
"""


def _q(
    key: str,
    name: str,
    display: str,
    description: str,
    tags: list[dict] | None = None,
    viz: dict | None = None,
) -> dict:
    return {
        "key": key,
        "name": name,
        "description": description,
        "display": display,
        "sql": f"{key}.sql",
        "tags": tags or [],
        "viz": viz or {},
    }


PERIOD = {
    "name": "period",
    "type": "dimension",
    "field": ["fct_pix_transactions", "month_start"],
    "widget": "date/all-options",
}
MED_PERIOD = {
    "name": "med_period",
    "type": "dimension",
    "field": ["fct_pix_med", "month_start"],
    "widget": "date/all-options",
}
REC_PERIOD = {
    "name": "receiver_period",
    "type": "dimension",
    "field": ["fct_pix_receiver_profile", "month_start"],
    "widget": "date/all-options",
}
MUNI_PERIOD = {
    "name": "period",
    "type": "dimension",
    "field": ["fct_pix_municipality", "month_start"],
    "widget": "date/all-options",
}
DICT_PERIOD = {
    "name": "period",
    "type": "dimension",
    "field": ["fct_pix_dict_users", "month_start"],
    "widget": "date/all-options",
}
KEYS_PERIOD = {
    "name": "period",
    "type": "dimension",
    "field": ["fct_pix_keys_stock", "month_start"],
    "widget": "date/all-options",
}
MEASURE = {"name": "measure", "type": "text", "default": "value", "required": True}
VIEW = {"name": "view", "type": "text", "default": "receiver", "required": True}
PERSON = {"name": "person", "type": "text", "default": "All", "required": True}
REGION = {"name": "region", "type": "text", "default": "All", "required": True}
STATE = {"name": "state", "type": "text", "default": "All", "required": True}
MUNI = {"name": "municipality", "type": "text", "default": "", "required": True}
PORTE = {"name": "porte", "type": "text", "default": "All", "required": True}
SECTION = {"name": "section", "type": "text", "default": "All", "required": True}
PTYPE = {"name": "person_type", "type": "text", "default": "All", "required": True}
MEI = {"name": "mei", "type": "text", "default": "All", "required": True}
MED_MEASURE = {"name": "med_measure", "type": "text", "default": "value", "required": True}

GEO = [MUNI_PERIOD, VIEW, PERSON, REGION, STATE, MUNI]
RECEIVER = [REC_PERIOD, PORTE, SECTION, PTYPE, MEI]


def currency(column: str) -> dict:
    return {
        f'["name","{column}"]': {
            "number_style": "currency",
            "currency": "BRL",
            "currency_style": "symbol",
            "decimals": 2,
        }
    }


def integer(column: str) -> dict:
    return {
        f'["name","{column}"]': {
            "number_style": "decimal",
            "decimals": 0,
        }
    }


def percent(column: str) -> dict:
    return {f'["name","{column}"]': {"number_style": "percent", "decimals": 2}}


QUESTIONS = [
    _q(
        "q1_tx_count",
        "How many SPI payments settled last complete month?",
        "smartscalar",
        "Sum of QUANTIDADE. The reference month is the latest complete month of EstatisticasTransacoesPix.",
        viz={"scalar.field": "transactions", "column_settings": integer("transactions")},
    ),
    _q(
        "q1_tx_value",
        "What value settled last complete month?",
        "smartscalar",
        "Sum of VALOR. SPI only.",
        viz={"scalar.field": "settled_value", "column_settings": currency("settled_value")},
    ),
    _q(
        "q1_ticket",
        "What was the average ticket last complete month?",
        "smartscalar",
        "sum(VALOR) / sum(QUANTIDADE) at the month grain.",
        viz={"scalar.field": "average_ticket", "column_settings": currency("average_ticket")},
    ),
    _q(
        "q1_dict_users",
        "How many DICT users were registered?",
        "object",
        "qtdUsuariosCadastradosDICTTotal for the latest complete snapshot. PF and PJ are the subtitle, not key counts.",
        viz={
            "column_settings": {
                **integer("dict_users"),
                **integer("pessoa_fisica"),
                **integer("pessoa_juridica"),
            }
        },
    ),
    _q(
        "q2_trend",
        "How did settled value and count move?",
        "combo",
        "SPI only. The open calendar month is excluded.",
        [PERIOD],
        {
            "graph.dimensions": ["month_start"],
            "graph.metrics": ["settled_value", "transactions"],
            "series_settings": {
                "settled_value": {"display": "line", "axis": "left"},
                "transactions": {"display": "bar", "axis": "right"},
            },
            "column_settings": {**currency("settled_value"), **integer("transactions")},
        },
    ),
    _q(
        "q3_natureza",
        "Who pays whom, by month?",
        "bar",
        "All NATUREZA codes. Default is value. Count is the same grain, not a second population.",
        [PERIOD, MEASURE],
        {
            "stackable.stack_type": "stacked",
            "graph.dimensions": ["month_start", "natureza"],
            "graph.metrics": ["amount"],
        },
    ),
    _q(
        "q3_matrix",
        "Who paid whom in the last complete month?",
        "table",
        "Rows are the receiver side (P, B, G). Columns are the payer side. The two sides are not added.",
        viz={
            "column_settings": {**currency("payer_p"), **currency("payer_b"), **currency("payer_g")}
        },
    ),
    _q(
        "q4_iniciacao",
        "How did the initiation mix shift?",
        "bar",
        "100% of settled value. DICT is a Pix key, QRDN a dynamic QR, QRES a static QR, MANU manual details, INIC a payment initiator. AUTO, APDN and APES stay codes. The raw token of an unstated row is in the label.",
        [PERIOD],
        {
            "stackable.stack_type": "normalized",
            "graph.dimensions": ["month_start", "forma_iniciacao_label"],
            "graph.metrics": ["settled_value"],
        },
    ),
    _q(
        "q4_finalidade",
        "Pix, Pix Saque or Pix Troco?",
        "table",
        "Finalidade is a table, not a primary chart. Nao disponivel stays visible.",
        [PERIOD],
        {"column_settings": {**currency("settled_value"), **integer("transactions")}},
    ),
    _q(
        "q5_users",
        "How did DICT users grow?",
        "line",
        "Total, natural persons and legal persons. These are users, not keys.",
        [DICT_PERIOD],
        {
            "graph.dimensions": ["month_start"],
            "graph.metrics": ["usuarios_total", "pessoa_fisica", "pessoa_juridica"],
            "column_settings": {
                **integer("usuarios_total"),
                **integer("pessoa_fisica"),
                **integer("pessoa_juridica"),
            },
        },
    ),
    _q(
        "q5_keys",
        "What is the month-end stock of keys by type?",
        "bar",
        "Month-end stock. Key counts are not user counts.",
        [KEYS_PERIOD],
        {
            "stackable.stack_type": "stacked",
            "graph.dimensions": ["month_start", "tipo_chave"],
            "graph.metrics": ["key_stock"],
            "column_settings": integer("key_stock"),
        },
    ),
    _q(
        "q5_participants",
        "Which participants hold the most keys?",
        "table",
        "Not a transaction-volume ranking. Stock of keys at the latest complete snapshot.",
        viz={"column_settings": integer("key_stock")},
    ),
    _q(
        "q6_kpi_value",
        "How much moved in this geography?",
        "scalar",
        "Receiver view by default. Payer and receiver are never added.",
        GEO,
        {"column_settings": currency("settled_value")},
    ),
    _q(
        "q6_kpi_payments",
        "How many payments moved in this geography?",
        "scalar",
        "Matches the value KPI's side and person type.",
        GEO,
        {"column_settings": integer("payments")},
    ),
    _q(
        "q6_kpi_people",
        "How many distinct people, in one municipality?",
        "scalar",
        "Shown only when the filter leaves a single municipality. Summing QT_PES across municipalities overcounts. No data for this period. means the selection is not one municipality.",
        GEO,
        {"column_settings": integer("distinct_people")},
    ),
    _q(
        "q6_region",
        "Which region moves the most?",
        "row",
        "Includes Nao informado, labeled Unstated / other with the raw token.",
        [MUNI_PERIOD, VIEW, PERSON, STATE, MUNI],
        {
            "graph.dimensions": ["regiao_label"],
            "graph.metrics": ["settled_value"],
            "column_settings": currency("settled_value"),
        },
    ),
    _q(
        "q6_state",
        "Which state moves the most?",
        "row",
        "Every UF plus NAO INFORMADO. Click a bar to set the state filter.",
        [MUNI_PERIOD, VIEW, PERSON, REGION, MUNI],
        {
            "graph.dimensions": ["state_label"],
            "graph.metrics": ["settled_value"],
            "column_settings": currency("settled_value"),
        },
    ),
    _q(
        "q6_table",
        "Which municipalities move the most?",
        "table",
        "Sorted by value. Distinct people is filled only when one municipality remains. N/D stays as Unstated.",
        GEO,
        {
            "table.pageSize": 25,
            "column_settings": {
                **currency("settled_value"),
                **integer("payments"),
                **currency("pessoa_fisica_value"),
                **currency("pessoa_juridica_value"),
                **integer("distinct_people"),
            },
        },
    ),
    _q(
        "q6_top",
        "Top 20 municipalities by value",
        "row",
        "Optional companion to the table.",
        GEO,
        {
            "graph.dimensions": ["municipality"],
            "graph.metrics": ["settled_value"],
            "column_settings": currency("settled_value"),
        },
    ),
    _q(
        "q8_age",
        "How old are the people paying or receiving?",
        "bar",
        "PF rows only. Nao informado stays. Nao se aplica is excluded. Blank when a state or municipality filter is set, because this series has no municipality grain.",
        [MUNI_PERIOD, VIEW, REGION, STATE, MUNI],
        {
            "graph.dimensions": ["age_band"],
            "graph.metrics": ["transactions"],
            "column_settings": integer("transactions"),
        },
    ),
    _q(
        "q8_notice",
        "Why is the age panel blank?",
        "scalar",
        "Shown when a state or municipality filter is active.",
        [STATE, MUNI],
    ),
    _q(
        "q7_flow",
        "Payer region → receiver region, last complete month",
        "table",
        "Optional matrix. Not a sum of the two sides: each cell is the flow from the payer region to the receiver region.",
        viz={"column_settings": currency("settled_value")},
    ),
    _q(
        "q9_kpi_value",
        "How much was settled to these receivers?",
        "scalar",
        "Sum of vllanliq. vlcompra and vldinespec are not used.",
        RECEIVER,
        {"column_settings": currency("settled_value")},
    ),
    _q(
        "q9_kpi_payments",
        "How many payments were settled to these receivers?",
        "scalar",
        "Sum of qtlanliq.",
        RECEIVER,
        {"column_settings": integer("payments")},
    ),
    _q(
        "q9_kpi_share",
        "What share of value went to micro and small firms?",
        "scalar",
        "porte in Microempresa or Pequeno Porte, over the other receiver filters. The porte filter does not apply to this share.",
        [REC_PERIOD, SECTION, PTYPE, MEI],
        {"column_settings": percent("micro_and_small_share")},
    ),
    _q(
        "q9_section",
        "Which CNAE sections received the value?",
        "row",
        "Pessoa fisica and Outros stay as their own bars.",
        [REC_PERIOD, PORTE, PTYPE, MEI],
        {
            "graph.dimensions": ["cnae_section"],
            "graph.metrics": ["settled_value"],
            "column_settings": currency("settled_value"),
        },
    ),
    _q(
        "q9_porte",
        "How is settled value split by firm size?",
        "bar",
        "Porte over time. A residual Outros is labeled Unstated / other.",
        [REC_PERIOD, SECTION, PTYPE, MEI],
        {
            "stackable.stack_type": "stacked",
            "graph.dimensions": ["month_start", "porte_label"],
            "graph.metrics": ["settled_value"],
        },
    ),
    _q(
        "q9_mei",
        "MEI, as published",
        "bar",
        "Field names are as published. S, N and Outros are not renamed.",
        [REC_PERIOD, PORTE, SECTION, PTYPE],
        {
            "graph.dimensions": ["mei_label"],
            "graph.metrics": ["settled_value"],
            "column_settings": currency("settled_value"),
        },
    ),
    _q(
        "q9_ticket_section",
        "What is the average ticket by CNAE section?",
        "row",
        "vllanliq / qtlanliq at the section grain.",
        [REC_PERIOD, PORTE, PTYPE, MEI],
        {
            "graph.dimensions": ["cnae_section"],
            "graph.metrics": ["average_ticket"],
            "column_settings": currency("average_ticket"),
        },
    ),
    _q(
        "q9_ticket_porte",
        "What is the average ticket by firm size?",
        "row",
        "vllanliq / qtlanliq at the porte grain.",
        [REC_PERIOD, SECTION, PTYPE, MEI],
        {
            "graph.dimensions": ["porte_label"],
            "graph.metrics": ["average_ticket"],
            "column_settings": currency("average_ticket"),
        },
    ),
    _q(
        "med_banner",
        "How current is MED?",
        "scalar",
        "MED is national, monthly, and published about 30 days after month-end.",
    ),
    _q(
        "med_gap",
        "Which MED month is missing?",
        "scalar",
        "A missing month is this sentence, not a zero.",
    ),
    _q(
        "med_contested",
        "How many PIX were contested via MED?",
        "smartscalar",
        "QtdePixcontestados. Not fraud cases.",
        viz={"scalar.field": "contested_via_med", "column_settings": integer("contested_via_med")},
    ),
    _q(
        "med_accepted",
        "How many contests were accepted, and what is the published per-100k rate?",
        "object",
        "Qtdecontestacoesaceitas and Qtdecontestacoesaceitasacada100mil as published. The rate is not recomputed.",
    ),
    _q(
        "med_percent",
        "What return rate did BCB publish?",
        "smartscalar",
        "PercentualdeDevolucao as published. Not recomputed.",
        viz={
            "scalar.field": "percentual_de_devolucao",
            "column_settings": {'["name","percentual_de_devolucao"]': {"decimals": 1}},
        },
    ),
    _q(
        "med_users",
        "How many users carry a fraud mark?",
        "smartscalar",
        "QtdeUsuarioscommarcacoesdefraude. A mark, not a fraud case.",
        viz={
            "scalar.field": "users_with_a_fraud_mark",
            "column_settings": integer("users_with_a_fraud_mark"),
        },
    ),
    _q(
        "med_keys",
        "How many keys carry a fraud mark?",
        "smartscalar",
        "QtdeChavesPixcommarcacoesdefraude. Keys, not users.",
        viz={
            "scalar.field": "keys_with_a_fraud_mark",
            "column_settings": integer("keys_with_a_fraud_mark"),
        },
    ),
    _q(
        "q10a",
        "Are contests, acceptances and the published return rate moving together?",
        "combo",
        "Axis starts at January 2022. Months BCB has not published are absent, not zero.",
        [MED_PERIOD],
        {
            "graph.dimensions": ["month_start"],
            "graph.metrics": ["contested_via_med", "accepted", "percentual_de_devolucao"],
            "series_settings": {
                "contested_via_med": {"display": "line", "axis": "left"},
                "accepted": {"display": "line", "axis": "left"},
                "percentual_de_devolucao": {"display": "line", "axis": "right"},
            },
            "column_settings": {**integer("contested_via_med"), **integer("accepted")},
        },
    ),
    _q(
        "q_ratio",
        "Is suspected fraud growing faster than Pix?",
        "line",
        RATIO_CAPTION,
        [MED_PERIOD],
        {
            "graph.dimensions": ["month_start"],
            "graph.metrics": ["accepted_value_over_spi"],
            "column_settings": percent("accepted_value_over_spi"),
        },
    ),
    _q(
        "q10b",
        "Why was value not returned, and how do returns compare?",
        "bar",
        "Last complete MED month. The first three bars are non-return reasons. Full and partial returns are a comparison, not reasons.",
        [MED_MEASURE],
        {"graph.dimensions": ["category"], "graph.metrics": ["amount"]},
    ),
]


def _param(pid: str, name: str, typ: str, default: object, values: list[str] | None = None) -> dict:
    body: dict = {"id": pid, "name": name, "slug": pid, "type": typ, "default": default}
    if default is None:
        body.pop("default")
    if values is not None:
        body["values_source_type"] = "static-list"
        body["values_source_config"] = {"values": values}
    return body


def _card(question: str, row: int, col: int, sx: int, sy: int, click: dict | None = None) -> dict:
    body = {"question": question, "row": row, "col": col, "size_x": sx, "size_y": sy}
    if click:
        body["click"] = click
    return body


def _text(row: int, text: str, sy: int = 2) -> dict:
    return {"row": row, "col": 0, "size_x": 24, "size_y": sy, "text": text}


REGIONS = [
    "All",
    "NORTE",
    "NORDESTE",
    "CENTRO-OESTE",
    "SUDESTE",
    "SUL",
    "Unstated / other (Nao informado)",
]
GEO_PARAMS = [
    _param("period", "Period", "date/all-options", "computed:transactions_last_12"),
    _param("region", "Region", "string/=", ["All"], REGIONS),
    _param("state", "State", "string/=", ["All"], ["All"]),
    _param("view", "Payer or receiver", "string/=", ["receiver"], ["receiver", "payer"]),
    _param("person", "Person type", "string/=", ["All"], ["All", "PF", "PJ"]),
    _param("municipality", "Municipality", "string/=", None),
]

collection = {
    "version": 1,
    "collection": "PIX Open Data",
    "questions_collection": "source questions",
    "database_name": "PIX marts",
    "duckdb_path": "/data/pix.duckdb",
    "footer": FOOTER,
    "empty_state": "No data for this period.",
    "questions": QUESTIONS,
    "dashboards": [
        {
            "key": "at_a_glance",
            "name": "PIX at a glance",
            "description": "National SPI picture for the last 12 complete months. KPIs stay on the latest complete month.",
            "width": "fixed",
            "parameters": [
                _param("period", "Period", "date/all-options", "computed:transactions_last_12"),
                _param("measure", "Value or count", "string/=", ["value"], ["value", "count"]),
            ],
            "cards": [
                _card("q1_tx_count", 0, 0, 6, 4),
                _card("q1_tx_value", 0, 6, 6, 4),
                _card("q1_ticket", 0, 12, 6, 4),
                _card("q1_dict_users", 0, 18, 6, 4),
                _card("q2_trend", 5, 0, 24, 8),
                _card("q3_natureza", 14, 0, 15, 8),
                _card("q3_matrix", 14, 15, 9, 8),
                _card("q4_iniciacao", 23, 0, 16, 8),
                _card("q4_finalidade", 23, 16, 8, 8),
                _card("q5_users", 32, 0, 24, 7),
                _card("q5_keys", 41, 0, 14, 8),
                _card("q5_participants", 41, 14, 10, 8),
            ],
            "texts": [
                _text(4, "SPI only. The open calendar month is excluded."),
                _text(40, "Month-end stock. Key counts are not user counts."),
                _text(49, "Not a transaction-volume ranking."),
                _text(51, FOOTER),
            ],
        },
        {
            "key": "where",
            "name": "Where it moves",
            "description": "Geography of PIX. Receiver view is the default. Payer and receiver are never added.",
            "width": "fixed",
            "parameters": GEO_PARAMS,
            "cards": [
                _card("q6_kpi_value", 0, 0, 8, 4),
                _card("q6_kpi_payments", 0, 8, 8, 4),
                _card("q6_kpi_people", 0, 16, 8, 4),
                _card("q6_region", 5, 0, 10, 8),
                _card("q6_state", 5, 10, 14, 8, {"column": "state_label", "parameter": "state"}),
                _card("q6_table", 14, 0, 24, 10),
                _card("q6_top", 25, 0, 24, 8),
                _card("q8_age", 34, 0, 16, 8),
                _card("q8_notice", 34, 16, 8, 4),
                _card("q7_flow", 43, 0, 24, 8),
            ],
            "texts": [_text(51, FOOTER)],
        },
        {
            "key": "receivers",
            "name": "Receivers and MED",
            "description": "Receiver profile from CnaePorteRecebedor, then national MED. MED has no geography filter.",
            "width": "fixed",
            "parameters": [
                _param(
                    "receiver_period",
                    "Receiver period",
                    "date/all-options",
                    "computed:transactions_last_12",
                ),
                _param(
                    "porte",
                    "Porte",
                    "string/=",
                    ["All"],
                    [
                        "All",
                        "Microempresa",
                        "Pequeno Porte",
                        "Media Empresa",
                        "Grande",
                        "Unstated / other (Nao informado)",
                    ],
                ),
                _param("section", "CNAE section", "string/=", ["All"]),
                _param("person_type", "Person type", "string/=", ["All"], ["All", "PF", "PJ"]),
                _param("mei", "MEI", "string/=", ["All"], ["All", "S", "N", "Outros"]),
                _param("med_period", "MED period", "date/all-options", "computed:med_full"),
                _param(
                    "med_measure", "MED value or count", "string/=", ["value"], ["value", "count"]
                ),
            ],
            "cards": [
                _card("q9_kpi_value", 2, 0, 8, 4),
                _card("q9_kpi_payments", 2, 8, 8, 4),
                _card("q9_kpi_share", 2, 16, 8, 4),
                _card("q9_section", 7, 0, 12, 8),
                _card("q9_ticket_section", 7, 12, 12, 8),
                _card("q9_porte", 16, 0, 12, 8),
                _card("q9_ticket_porte", 16, 12, 12, 8),
                _card("q9_mei", 25, 0, 24, 7),
                _card("med_banner", 36, 0, 16, 3),
                _card("med_gap", 36, 16, 8, 3),
                _card("med_contested", 40, 0, 8, 4),
                _card("med_accepted", 40, 8, 8, 4),
                _card("med_percent", 40, 16, 8, 4),
                _card("med_users", 45, 0, 12, 4),
                _card("med_keys", 45, 12, 12, 4),
                _card("q10a", 50, 0, 24, 8),
                _card("q_ratio", 60, 0, 24, 8),
                _card("q10b", 70, 0, 24, 8),
            ],
            "texts": [
                _text(
                    0,
                    "Receivers. Settled value is vllanliq. Purchase value, cash and same-ownership are not on this dashboard.",
                ),
                _text(24, "Field names are as published."),
                _text(
                    33, "MED. Figures are national and monthly. There is no municipality filter."
                ),
                _text(59, RATIO_CAPTION),
                _text(79, FOOTER),
            ],
        },
    ],
}


def main() -> None:
    sql_dir = ROOT / "sql"
    sql_dir.mkdir(parents=True, exist_ok=True)
    for key, body in SQL.items():
        (sql_dir / f"{key}.sql").write_text(body.strip() + "\n", encoding="utf-8")
    (ROOT / "collection.json").write_text(json.dumps(collection, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(SQL)} questions")


if __name__ == "__main__":
    main()
