select cast(municipio_ibge as varchar), municipio_raw, municipio_label
from {{ ref('fct_pix_municipality') }}
where municipio_ibge = 0
    and (
        municipio_raw <> 'N/D'
        or municipio_label <> 'Unstated / other (N/D)'
    )

union all

select 'column', column_name, 'forbidden'
from information_schema.columns
where table_schema = 'marts'
    and table_name = 'fct_pix_municipality'
    and column_name in ('valor', 'quantidade', 'valor_total', 'quantidade_total')
