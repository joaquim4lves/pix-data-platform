select
    municipio_label as municipality,
    sum(
        case
            when {{person}} = 'PF' and {{view}} = 'payer' then valor_pagador_pf
            when {{person}} = 'PJ' and {{view}} = 'payer' then valor_pagador_pj
            when {{view}} = 'payer' then valor_pagador
            when {{person}} = 'PF' then valor_recebedor_pf
            when {{person}} = 'PJ' then valor_recebedor_pj
            else valor_recebedor
        end
    ) as settled_value
from marts.fct_pix_municipality
where is_complete_month
[[and {{period}}]]
and ({{region}} = 'All' or regiao_label = {{region}})
and ({{state}} = 'All' or state_label = {{state}})
and ({{municipality}} = '' or lower(municipio_label) like '%' || lower({{municipality}}) || '%')
group by municipio_label
order by settled_value desc
limit 20
