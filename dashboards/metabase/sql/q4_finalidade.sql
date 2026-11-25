select
    finalidade_label,
    finalidade_raw,
    sum(valor) as settled_value,
    cast(round(sum(quantidade)) as bigint) as transactions
from marts.fct_pix_transactions
where is_complete_month
[[and {{period}}]]
group by finalidade_label, finalidade_raw
order by settled_value desc
