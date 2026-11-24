-- Pessoa física / pessoa jurídica. Used by payer, receiver, and key holder.
-- Grain: codigo.

with observed as (
    select distinct codigo
    from (
        select pagador_tipo_pessoa as codigo
        from intermediate.int_transacoes_mensal
        union
        select recebedor_tipo_pessoa as codigo
        from intermediate.int_transacoes_mensal
        union
        select natureza_usuario as codigo
        from intermediate.int_chaves_pix
    ) as codes
    where codigo is not null
)
select
    coalesce(seed.codigo, observed.codigo) as codigo,
    coalesce(seed.rotulo, observed.codigo) as rotulo,
    coalesce(seed.fonte, 'raw') as fonte
from seeds.seed_tipo_pessoa as seed
full outer join observed
    on seed.codigo = observed.codigo
