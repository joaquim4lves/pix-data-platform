select 'dim_tempo' as dimension_name, cast(ano_mes as varchar) as key_value, count(*) as rows
from marts.dim_tempo
group by ano_mes
having count(*) > 1
union all
select 'dim_municipio', cast(municipio_ibge as varchar), count(*)
from marts.dim_municipio
group by municipio_ibge
having count(*) > 1
union all
select 'dim_natureza', codigo, count(*)
from marts.dim_natureza
group by codigo
having count(*) > 1
union all
select 'dim_forma_iniciacao', codigo, count(*)
from marts.dim_forma_iniciacao
group by codigo
having count(*) > 1
union all
select 'dim_finalidade', codigo, count(*)
from marts.dim_finalidade
group by codigo
having count(*) > 1
union all
select 'dim_faixa_idade', codigo, count(*)
from marts.dim_faixa_idade
group by codigo
having count(*) > 1
union all
select 'dim_tipo_pessoa', codigo, count(*)
from marts.dim_tipo_pessoa
group by codigo
having count(*) > 1
union all
select 'dim_regiao', codigo, count(*)
from marts.dim_regiao
group by codigo
having count(*) > 1
union all
select 'dim_tipo_chave', codigo, count(*)
from marts.dim_tipo_chave
group by codigo
having count(*) > 1
union all
select 'dim_instituicao', ispb, count(*)
from marts.dim_instituicao
group by ispb
having count(*) > 1
