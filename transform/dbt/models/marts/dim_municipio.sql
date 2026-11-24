-- One row per municipality, including municipio_ibge 0 ("Não informado").
-- Attributes come from the latest month in the extract. UF sigla and the
-- display name of the state come from the IBGE seed when the code matches.
-- The raw municipality name is kept (Olinda publishes it in uppercase).
-- Grain: municipio_ibge.

with ranked as (
    select
        municipio_ibge,
        nome,
        nome_fonte,
        uf_ibge,
        uf_nome_fonte,
        sigla_regiao,
        regiao_nome_fonte,
        row_number() over (
            partition by municipio_ibge
            order by ano_mes desc
        ) as rn
    from {{ ref('int_transacoes_municipio') }}
)
select
    ranked.municipio_ibge,
    ranked.nome,
    ranked.nome_fonte,
    ranked.uf_ibge,
    uf.sigla as uf_sigla,
    coalesce(uf.nome, ranked.uf_nome_fonte) as uf_nome,
    coalesce(uf.sigla_regiao, ranked.sigla_regiao) as sigla_regiao,
    coalesce(uf.regiao_nome, ranked.regiao_nome_fonte) as regiao_nome
from ranked
left join {{ ref('seed_uf') }} as uf
    on ranked.uf_ibge = uf.uf_ibge
where ranked.rn = 1
