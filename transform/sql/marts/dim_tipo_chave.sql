-- PIX key type. The key is the TipoChave string Olinda returns.
-- Grain: codigo.

with observed as (
    select distinct tipo_chave as codigo
    from intermediate.int_chaves_pix
    where tipo_chave is not null
)
select
    coalesce(seed.codigo, observed.codigo) as codigo,
    coalesce(seed.rotulo, observed.codigo) as rotulo,
    seed.ordem as ordem,
    coalesce(seed.fonte, 'raw') as fonte
from seeds.seed_tipo_chave as seed
full outer join observed
    on seed.codigo = observed.codigo
