-- A raw municipality row with a null IBGE code has to survive as the
-- explicit "Não informado" member (municipio_ibge 0). Dropping it fails
-- this check.

select staged.ano_mes
from {{ ref('stg_transacoes_pix_municipio') }} as staged
where staged.municipio_ibge is null
    and not exists (
        select 1
        from {{ ref('dim_municipio') }} as dim
        where dim.municipio_ibge = 0
            and dim.nome = 'Não informado'
    )
