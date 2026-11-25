select
    month_start as reference_month,
    usuarios_total as dict_users,
    usuarios_pf as pessoa_fisica,
    usuarios_pj as pessoa_juridica
from marts.fct_pix_dict_users
where is_complete_month
order by month_start desc
limit 1
