-- Macro-region of the payer or the receiver on the national extract.
-- The key is the raw string (NORDESTE, "Nao informado", ...), so the fact
-- joins without a translation table. Grain: codigo.

with observed as (
    select distinct regiao as codigo
    from (
        select pagador_regiao as regiao
        from intermediate.int_transacoes_mensal
        union
        select recebedor_regiao as regiao
        from intermediate.int_transacoes_mensal
    ) as regions
    where regiao is not null
)
select
    coalesce(seed.codigo, observed.codigo) as codigo,
    coalesce(seed.rotulo, observed.codigo) as rotulo,
    seed.sigla as sigla,
    coalesce(seed.fonte, 'raw') as fonte
from seeds.seed_regiao as seed
full outer join observed
    on seed.codigo = observed.codigo
