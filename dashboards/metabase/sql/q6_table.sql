with filtered as (
    select *
    from marts.fct_pix_municipality
    where is_complete_month
    [[and {{period}}]]
    and ({{region}} = 'All' or regiao_label = {{region}})
    and ({{state}} = 'All' or state_label = {{state}})
    and ({{municipality}} = '' or lower(municipio_label) like '%' || lower({{municipality}}) || '%')
),
rolled as (
    select
        municipio_label,
        municipio_raw,
        state_label,
        regiao_label,
        sum(
            case
                when {{person}} = 'PF' and {{view}} = 'payer' then valor_pagador_pf
                when {{person}} = 'PJ' and {{view}} = 'payer' then valor_pagador_pj
                when {{view}} = 'payer' then valor_pagador
                when {{person}} = 'PF' then valor_recebedor_pf
                when {{person}} = 'PJ' then valor_recebedor_pj
                else valor_recebedor
            end
        ) as settled_value,
        cast(round(sum(
            case
                when {{person}} = 'PF' and {{view}} = 'payer' then quantidade_pagador_pf
                when {{person}} = 'PJ' and {{view}} = 'payer' then quantidade_pagador_pj
                when {{view}} = 'payer' then quantidade_pagador
                when {{person}} = 'PF' then quantidade_recebedor_pf
                when {{person}} = 'PJ' then quantidade_recebedor_pj
                else quantidade_recebedor
            end
        )) as bigint) as payments,
        sum(case when {{view}} = 'payer' then valor_pagador_pf else valor_recebedor_pf end) as pessoa_fisica_value,
        sum(case when {{view}} = 'payer' then valor_pagador_pj else valor_recebedor_pj end) as pessoa_juridica_value,
        sum(
            case
                when {{person}} = 'PF' and {{view}} = 'payer' then pessoas_pagador_pf
                when {{person}} = 'PJ' and {{view}} = 'payer' then pessoas_pagador_pj
                when {{view}} = 'payer' then pessoas_pagador
                when {{person}} = 'PF' then pessoas_recebedor_pf
                when {{person}} = 'PJ' then pessoas_recebedor_pj
                else pessoas_recebedor
            end
        ) as distinct_people_row
    from filtered
    group by municipio_label, municipio_raw, state_label, regiao_label
)
select
    municipio_label as municipality,
    municipio_raw,
    state_label as state,
    regiao_label as region,
    settled_value,
    payments,
    pessoa_fisica_value,
    pessoa_juridica_value,
    case when count(*) over () = 1 then distinct_people_row else null end as distinct_people
from rolled
order by settled_value desc
