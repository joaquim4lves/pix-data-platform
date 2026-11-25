select ano_mes, usuarios_pf, usuarios_pj, usuarios_total
from {{ ref('fct_pix_dict_users') }}
where usuarios_total <> usuarios_pf + usuarios_pj
    or usuarios_total < 0
