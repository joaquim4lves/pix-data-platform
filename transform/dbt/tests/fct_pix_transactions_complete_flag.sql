select ano_mes, is_complete_month
from {{ ref('fct_pix_transactions') }}
where is_complete_month <> {{ is_complete_month('ano_mes') }}
