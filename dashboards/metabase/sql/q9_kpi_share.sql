select
    sum(case when porte_raw in ('Microempresa', 'Pequeno Porte') then valor_liquidado else 0 end)
        / nullif(sum(valor_liquidado), 0) as micro_and_small_share
from marts.fct_pix_receiver_profile
where is_complete_month
[[and {{receiver_period}}]]
and ({{section}} = 'All' or cnae_secao_label = {{section}})
and ({{person_type}} = 'All' or tipo_pessoa = {{person_type}})
and ({{mei}} = 'All' or mei_label = {{mei}})
