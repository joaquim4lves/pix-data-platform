-- One row per natureza code.
-- Seed labels, plus any code that appears in the extract and is missing
-- from the seed. An unknown code keeps the raw value as rotulo and
-- publicado = false, so a tenth code is not dropped.
-- Grain: codigo.

with observed as (
    select distinct natureza as codigo
    from {{ ref('int_transacoes_mensal') }}
    where natureza is not null
)
select
    coalesce(seed.codigo, observed.codigo) as codigo,
    coalesce(seed.rotulo, observed.codigo) as rotulo,
    seed.descricao as descricao,
    coalesce(seed.publicado, false) as publicado,
    coalesce(seed.fonte, 'raw') as fonte
from {{ ref('seed_natureza') }} as seed
full outer join observed
    on seed.codigo = observed.codigo
