select
    porte_label,
    sum(valor_liquidado) / nullif(sum(quantidade_liquidada), 0) as average_ticket
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{section}} = 'All' or cnae_secao_label = {{section}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
and ({{mei}} = 'All' or mei_label = {{mei}})
group by porte_label
order by average_ticket desc
