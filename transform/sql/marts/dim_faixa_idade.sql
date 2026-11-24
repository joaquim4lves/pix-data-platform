-- One row per age band as Olinda spells it.
-- Grain: codigo. ordem is null for a band that is not in the seed.

with observed as (
    select distinct faixa as codigo
    from (
        select pagador_faixa_idade as faixa
        from intermediate.int_transacoes_mensal
        union
        select recebedor_faixa_idade as faixa
        from intermediate.int_transacoes_mensal
    ) as bands
    where faixa is not null
)
select
    coalesce(seed.codigo, observed.codigo) as codigo,
    coalesce(seed.rotulo, observed.codigo) as rotulo,
    seed.ordem as ordem,
    coalesce(seed.fonte, 'raw') as fonte
from seeds.seed_faixa_idade as seed
full outer join observed
    on seed.codigo = observed.codigo
