select column_name
from information_schema.columns
where table_schema = 'marts'
    and table_name = 'fct_pix_receiver_profile'
    and column_name in (
        'valor_compra',
        'valor_dinheiro_especie',
        'mesmo_titular',
        'vlcompra',
        'vldinespec',
        'mesmatit'
    )

union all

select cnae_secao_raw
from {{ ref('fct_pix_receiver_profile') }}
where cnae_secao_raw in ('Pessoa fisica', 'Outros')
    and cnae_secao_label <> cnae_secao_raw

union all

select mei_raw
from {{ ref('fct_pix_receiver_profile') }}
where mei_raw = 'Outros'
    and mei_label <> 'Outros'
