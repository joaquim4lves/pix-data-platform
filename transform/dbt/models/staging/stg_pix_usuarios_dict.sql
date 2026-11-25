-- Typed PixUsuariosCadastradosDICT. The snapshot date is the last
-- calendar day of the month. These are registered users, not keys.

select
    cast("DataGraficosPix" as date) as data_referencia,
    cast(substr(cast(cast("DataGraficosPix" as date) as varchar), 1, 4) as integer) * 100
        + cast(substr(cast(cast("DataGraficosPix" as date) as varchar), 6, 2) as integer) as ano_mes,
    cast("qtdUsuariosPessoaFisica" as bigint) as usuarios_pf,
    cast("qtdUsuariosPessoaJuridica" as bigint) as usuarios_pj,
    cast("qtdUsuariosCadastradosDICTTotal" as bigint) as usuarios_total
from {{ source('raw', 'pix_usuarios_dict') }}
where "DataGraficosPix" is not null
