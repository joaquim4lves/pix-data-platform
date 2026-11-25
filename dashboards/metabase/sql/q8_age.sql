select
    case when {{view}} = 'payer' then pagador_idade_label else recebedor_idade_label end as age_band,
    case when {{view}} = 'payer' then pagador_idade_raw else recebedor_idade_raw end as raw_token,
    cast(round(sum(quantidade)) as bigint) as transactions
from marts.fct_pix_transactions
where is_complete_month
    and {{state}} = 'All'
    and {{municipality}} = ''
    and ({{region}} = 'All' or (
        ({{view}} = 'payer' and pagador_regiao_label = {{region}})
        or ({{view}} <> 'payer' and recebedor_regiao_label = {{region}})
    ))
    and (
        ({{view}} = 'payer' and pagador_tipo_pessoa = 'PF' and pagador_idade_raw <> 'Nao se aplica')
        or ({{view}} <> 'payer' and recebedor_tipo_pessoa = 'PF' and recebedor_idade_raw <> 'Nao se aplica')
    )
[[and {{period}}]]
group by 1, 2
order by transactions desc
