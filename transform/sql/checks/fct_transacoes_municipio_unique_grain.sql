-- Grain: one row per month and municipality, including ibge 0.

select
    ano_mes,
    municipio_ibge,
    count(*) as rows
from marts.fct_transacoes_municipio
group by
    ano_mes,
    municipio_ibge
having count(*) > 1
