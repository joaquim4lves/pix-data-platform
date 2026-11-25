select cast(round(sum(
    case
        when {{person}} = 'PF' and {{view}} = 'payer' then quantidade_pagador_pf
        when {{person}} = 'PJ' and {{view}} = 'payer' then quantidade_pagador_pj
        when {{view}} = 'payer' then quantidade_pagador
        when {{person}} = 'PF' then quantidade_recebedor_pf
        when {{person}} = 'PJ' then quantidade_recebedor_pj
        else quantidade_recebedor
    end
)) as bigint) as payments
from marts.fct_pix_municipality
where is_complete_month
[[and {{period}}]]
and ({{region}} = 'All' or regiao_label = {{region}})
and ({{state}} = 'All' or state_label = {{state}})
and ({{municipality}} = '' or lower(municipio_label) like '%' || lower({{municipality}}) || '%')
