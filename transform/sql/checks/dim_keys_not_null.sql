select 'dim_tempo.ano_mes' as column_name
from marts.dim_tempo
where ano_mes is null
union all
select 'dim_municipio.municipio_ibge'
from marts.dim_municipio
where municipio_ibge is null
union all
select 'dim_municipio.nome'
from marts.dim_municipio
where nome is null
union all
select 'dim_natureza.codigo'
from marts.dim_natureza
where codigo is null
union all
select 'dim_forma_iniciacao.codigo'
from marts.dim_forma_iniciacao
where codigo is null
union all
select 'dim_finalidade.codigo'
from marts.dim_finalidade
where codigo is null
union all
select 'dim_faixa_idade.codigo'
from marts.dim_faixa_idade
where codigo is null
union all
select 'dim_tipo_pessoa.codigo'
from marts.dim_tipo_pessoa
where codigo is null
union all
select 'dim_regiao.codigo'
from marts.dim_regiao
where codigo is null
union all
select 'dim_tipo_chave.codigo'
from marts.dim_tipo_chave
where codigo is null
union all
select 'dim_instituicao.ispb'
from marts.dim_instituicao
where ispb is null
