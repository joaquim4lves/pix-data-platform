select 'ano_mes' as key_name, cast(fct.ano_mes as varchar) as key_value
from marts.fct_transacoes_mensal as fct
left join marts.dim_tempo as dim
    on fct.ano_mes = dim.ano_mes
where dim.ano_mes is null
union all
select 'natureza', fct.natureza
from marts.fct_transacoes_mensal as fct
left join marts.dim_natureza as dim
    on fct.natureza = dim.codigo
where dim.codigo is null
union all
select 'forma_iniciacao', fct.forma_iniciacao
from marts.fct_transacoes_mensal as fct
left join marts.dim_forma_iniciacao as dim
    on fct.forma_iniciacao = dim.codigo
where dim.codigo is null
union all
select 'finalidade', fct.finalidade
from marts.fct_transacoes_mensal as fct
left join marts.dim_finalidade as dim
    on fct.finalidade = dim.codigo
where dim.codigo is null
union all
select 'pagador_tipo_pessoa', fct.pagador_tipo_pessoa
from marts.fct_transacoes_mensal as fct
left join marts.dim_tipo_pessoa as dim
    on fct.pagador_tipo_pessoa = dim.codigo
where dim.codigo is null
union all
select 'recebedor_tipo_pessoa', fct.recebedor_tipo_pessoa
from marts.fct_transacoes_mensal as fct
left join marts.dim_tipo_pessoa as dim
    on fct.recebedor_tipo_pessoa = dim.codigo
where dim.codigo is null
union all
select 'pagador_regiao', fct.pagador_regiao
from marts.fct_transacoes_mensal as fct
left join marts.dim_regiao as dim
    on fct.pagador_regiao = dim.codigo
where dim.codigo is null
union all
select 'recebedor_regiao', fct.recebedor_regiao
from marts.fct_transacoes_mensal as fct
left join marts.dim_regiao as dim
    on fct.recebedor_regiao = dim.codigo
where dim.codigo is null
union all
select 'pagador_faixa_idade', fct.pagador_faixa_idade
from marts.fct_transacoes_mensal as fct
left join marts.dim_faixa_idade as dim
    on fct.pagador_faixa_idade = dim.codigo
where dim.codigo is null
union all
select 'recebedor_faixa_idade', fct.recebedor_faixa_idade
from marts.fct_transacoes_mensal as fct
left join marts.dim_faixa_idade as dim
    on fct.recebedor_faixa_idade = dim.codigo
where dim.codigo is null
