select month_start, usuarios_total, usuarios_pf as pessoa_fisica, usuarios_pj as pessoa_juridica
from marts.fct_pix_dict_users
where is_complete_month
[[and {{period}}]]
order by month_start
