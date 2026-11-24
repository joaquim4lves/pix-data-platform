-- A raw municipality row with a null IBGE code has to survive as the
-- explicit "Não informado" member (municipio_ibge 0). Dropping it fails
-- this check.

select staging.ano_mes
from staging.stg_transacoes_pix_municipio as staging
where staging.municipio_ibge is null
    and not exists (
        select 1
        from marts.dim_municipio as dim
        where dim.municipio_ibge = 0
            and dim.nome = 'Não informado'
    )
