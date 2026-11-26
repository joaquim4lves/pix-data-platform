select mei_label, mei_raw, sum(valor_liquidado) as settled_value
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{porte}} = 'All' or porte_label = {{porte}})
and ({{section}} = 'All' or cnae_secao_label = {{section}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
group by mei_label, mei_raw
order by settled_value desc
