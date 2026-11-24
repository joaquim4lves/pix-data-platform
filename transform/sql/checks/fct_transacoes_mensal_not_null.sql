select 'ano_mes' as column_name
from marts.fct_transacoes_mensal
where ano_mes is null
union all
select 'pagador_tipo_pessoa'
from marts.fct_transacoes_mensal
where pagador_tipo_pessoa is null
union all
select 'recebedor_tipo_pessoa'
from marts.fct_transacoes_mensal
where recebedor_tipo_pessoa is null
union all
select 'pagador_regiao'
from marts.fct_transacoes_mensal
where pagador_regiao is null
union all
select 'recebedor_regiao'
from marts.fct_transacoes_mensal
where recebedor_regiao is null
union all
select 'pagador_faixa_idade'
from marts.fct_transacoes_mensal
where pagador_faixa_idade is null
union all
select 'recebedor_faixa_idade'
from marts.fct_transacoes_mensal
where recebedor_faixa_idade is null
union all
select 'forma_iniciacao'
from marts.fct_transacoes_mensal
where forma_iniciacao is null
union all
select 'natureza'
from marts.fct_transacoes_mensal
where natureza is null
union all
select 'finalidade'
from marts.fct_transacoes_mensal
where finalidade is null
union all
select 'valor'
from marts.fct_transacoes_mensal
where valor is null
union all
select 'quantidade'
from marts.fct_transacoes_mensal
where quantidade is null
