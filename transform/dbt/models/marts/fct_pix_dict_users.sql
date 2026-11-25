-- Registered DICT users at month end. One row per snapshot.
-- usuarios_total is the published total, not a count of keys.

select
    ano_mes,
    {{ month_start('ano_mes') }} as month_start,
    {{ is_complete_month('ano_mes') }} as is_complete_month,
    data_referencia,
    usuarios_pf,
    usuarios_pj,
    usuarios_total
from {{ ref('stg_pix_usuarios_dict') }}
