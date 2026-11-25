select cnae_secao_label as cnae_section, cnae_secao_raw, sum(valor_liquidado) as settled_value
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{porte}} = 'All' or porte_label = {{porte}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
and ({{mei}} = 'All' or mei_label = {{mei}})
group by cnae_secao_label, cnae_secao_raw
order by settled_value desc
