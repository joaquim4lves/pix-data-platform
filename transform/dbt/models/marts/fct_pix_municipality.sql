-- Municipality month for the geography dashboard.
-- valor_pagador is PF+PJ on the payer side. valor_recebedor is PF+PJ
-- on the receiver side. The two sides are not added. pessoas_* are
-- distinct people inside this municipality-month and are not a national
-- count when summed across municipalities.
-- The published N/D row stays, labeled Unstated / other, with the raw token.

select
    base.ano_mes,
    {{ month_start('base.ano_mes') }} as month_start,
    {{ is_complete_month('base.ano_mes') }} as is_complete_month,
    base.municipio_ibge,
    base.nome_fonte as municipio_raw,
    case
        when base.municipio_ibge = 0 then 'Unstated / other (' || base.nome_fonte || ')'
        else base.nome
    end as municipio_label,
    base.uf_ibge,
    base.uf_nome_fonte as uf_raw,
    case
        when base.uf_ibge = 0 then 'Unstated / other (' || base.uf_nome_fonte || ')'
        else coalesce(dim.uf_sigla, base.uf_nome_fonte)
    end as state_label,
    coalesce(dim.uf_nome, base.uf_nome_fonte) as uf_nome,
    base.regiao_nome_fonte as regiao_raw,
    {{ label_with_token('base.regiao_nome_fonte') }} as regiao_label,
    base.valor_pagador_pf,
    base.quantidade_pagador_pf,
    base.valor_pagador_pj,
    base.quantidade_pagador_pj,
    base.valor_pagador_pf + base.valor_pagador_pj as valor_pagador,
    base.quantidade_pagador_pf + base.quantidade_pagador_pj as quantidade_pagador,
    base.valor_recebedor_pf,
    base.quantidade_recebedor_pf,
    base.valor_recebedor_pj,
    base.quantidade_recebedor_pj,
    base.valor_recebedor_pf + base.valor_recebedor_pj as valor_recebedor,
    base.quantidade_recebedor_pf + base.quantidade_recebedor_pj as quantidade_recebedor,
    base.quantidade_pessoas_pagador_pf as pessoas_pagador_pf,
    base.quantidade_pessoas_pagador_pj as pessoas_pagador_pj,
    base.quantidade_pessoas_pagador_pf + base.quantidade_pessoas_pagador_pj as pessoas_pagador,
    base.quantidade_pessoas_recebedor_pf as pessoas_recebedor_pf,
    base.quantidade_pessoas_recebedor_pj as pessoas_recebedor_pj,
    base.quantidade_pessoas_recebedor_pf
        + base.quantidade_pessoas_recebedor_pj as pessoas_recebedor
from {{ ref('int_transacoes_municipio') }} as base
left join {{ ref('dim_municipio') }} as dim
    on base.municipio_ibge = dim.municipio_ibge
