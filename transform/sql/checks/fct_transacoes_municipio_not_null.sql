select 'ano_mes' as column_name
from marts.fct_transacoes_municipio
where ano_mes is null
union all
select 'municipio_ibge'
from marts.fct_transacoes_municipio
where municipio_ibge is null
union all
select 'valor_enviado'
from marts.fct_transacoes_municipio
where valor_enviado is null
union all
select 'valor_recebido'
from marts.fct_transacoes_municipio
where valor_recebido is null
union all
select 'quantidade_enviada'
from marts.fct_transacoes_municipio
where quantidade_enviada is null
union all
select 'quantidade_recebida'
from marts.fct_transacoes_municipio
where quantidade_recebida is null
