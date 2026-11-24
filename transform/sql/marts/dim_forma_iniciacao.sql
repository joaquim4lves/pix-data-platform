-- One row per initiation-form code, including "Nao disponivel".
-- Unknown codes from the extract are kept with rotulo = codigo.
-- Grain: codigo.

with observed as (
    select distinct forma_iniciacao as codigo
    from intermediate.int_transacoes_mensal
    where forma_iniciacao is not null
)
select
    coalesce(seed.codigo, observed.codigo) as codigo,
    coalesce(seed.rotulo, observed.codigo) as rotulo,
    coalesce(seed.publicado, false) as publicado,
    coalesce(seed.fonte, 'raw') as fonte
from seeds.seed_forma_iniciacao as seed
full outer join observed
    on seed.codigo = observed.codigo
