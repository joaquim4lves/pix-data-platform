select column_name
from information_schema.columns
where table_schema = 'marts'
    and table_name = 'fct_pix_keys_stock'
    and (
        lower(column_name) like '%usuarios%'
        or lower(column_name) in ('users', 'user_count', 'qtd_usuarios')
    )

union all

select cast(ano_mes as varchar)
from {{ ref('fct_pix_keys_stock') }}
where quantidade_chaves < 0
