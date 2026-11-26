select month_start, forma_iniciacao_label, forma_iniciacao_raw, sum(valor) as settled_value
from marts.fct_pix_transactions
where is_complete_month
[[and {{period}}]]
group by month_start, forma_iniciacao_label, forma_iniciacao_raw
order by month_start, forma_iniciacao_label
