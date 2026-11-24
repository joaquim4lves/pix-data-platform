-- One row per finalidade, including "Nao disponivel".
-- Grain: codigo.

with observed as (
    select distinct finalidade as codigo
    from {{ ref('int_transacoes_mensal') }}
    where finalidade is not null
)
select
    coalesce(seed.codigo, observed.codigo) as codigo,
    coalesce(seed.rotulo, observed.codigo) as rotulo,
    coalesce(seed.fonte, 'raw') as fonte
from {{ ref('seed_finalidade') }} as seed
full outer join observed
    on seed.codigo = observed.codigo
