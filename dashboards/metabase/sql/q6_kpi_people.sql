with filtered as (
    select
        municipio_ibge,
        sum(
            case
                when {{person}} = 'PF' and {{view}} = 'payer' then pessoas_pagador_pf
                when {{person}} = 'PJ' and {{view}} = 'payer' then pessoas_pagador_pj
                when {{view}} = 'payer' then pessoas_pagador
                when {{person}} = 'PF' then pessoas_recebedor_pf
                when {{person}} = 'PJ' then pessoas_recebedor_pj
                else pessoas_recebedor
            end
        ) as pessoas
    from marts.fct_pix_municipality
    where is_complete_month
    [[and {{period}}]]
    and ({{region}} = 'All' or regiao_label = {{region}})
    and ({{state}} = 'All' or state_label = {{state}})
    and ({{municipality}} = '' or lower(municipio_label) like '%' || lower({{municipality}}) || '%')
    group by municipio_ibge
)
select cast(round(sum(pessoas)) as bigint) as distinct_people
from filtered
having count(*) = 1
