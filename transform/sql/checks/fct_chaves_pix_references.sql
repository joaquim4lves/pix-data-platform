select 'ano_mes' as key_name, cast(fct.ano_mes as varchar) as key_value
from marts.fct_chaves_pix as fct
left join marts.dim_tempo as dim
    on fct.ano_mes = dim.ano_mes
where dim.ano_mes is null
union all
select 'ispb', fct.ispb
from marts.fct_chaves_pix as fct
left join marts.dim_instituicao as dim
    on fct.ispb = dim.ispb
where dim.ispb is null
union all
select 'tipo_chave', fct.tipo_chave
from marts.fct_chaves_pix as fct
left join marts.dim_tipo_chave as dim
    on fct.tipo_chave = dim.codigo
where dim.codigo is null
union all
select 'natureza_usuario', fct.natureza_usuario
from marts.fct_chaves_pix as fct
left join marts.dim_tipo_pessoa as dim
    on fct.natureza_usuario = dim.codigo
where dim.codigo is null
