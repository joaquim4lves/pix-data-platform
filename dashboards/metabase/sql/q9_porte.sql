select month_start, porte_label, porte_raw, sum(valor_liquidado) as settled_value
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{section}} = 'All' or cnae_secao_label = {{section}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
and ({{mei}} = 'All' or mei_label = {{mei}})
group by month_start, porte_label, porte_raw
order by month_start, porte_label
