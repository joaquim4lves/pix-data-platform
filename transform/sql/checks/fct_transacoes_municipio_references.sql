select 'ano_mes' as key_name, cast(fct.ano_mes as varchar) as key_value
from marts.fct_transacoes_municipio as fct
left join marts.dim_tempo as dim
    on fct.ano_mes = dim.ano_mes
where dim.ano_mes is null
union all
select 'municipio_ibge', cast(fct.municipio_ibge as varchar)
from marts.fct_transacoes_municipio as fct
left join marts.dim_municipio as dim
    on fct.municipio_ibge = dim.municipio_ibge
where dim.municipio_ibge is null
