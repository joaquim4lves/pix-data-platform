select 'ano_mes' as column_name
from marts.fct_chaves_pix
where ano_mes is null
union all
select 'data_referencia'
from marts.fct_chaves_pix
where data_referencia is null
union all
select 'ispb'
from marts.fct_chaves_pix
where ispb is null
union all
select 'natureza_usuario'
from marts.fct_chaves_pix
where natureza_usuario is null
union all
select 'tipo_chave'
from marts.fct_chaves_pix
where tipo_chave is null
union all
select 'quantidade_chaves'
from marts.fct_chaves_pix
where quantidade_chaves is null
