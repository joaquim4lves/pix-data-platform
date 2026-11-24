-- Municipality month, with the published N/D bucket kept.
-- municipio_ibge 0 and uf_ibge 0 mean "Não informado". IBGE does not
-- assign 0. The raw row has null codes and Municipio = 'N/D' (see
-- docs/spike-bcb.md). A row named N/D is mapped the same way even if a
-- code appears later, so that label cannot become a city.

select
    ano_mes,
    case
        when municipio_ibge is null or upper(municipio) in ('N/D', 'ND') then 0
        else municipio_ibge
    end as municipio_ibge,
    case
        when municipio_ibge is null or upper(municipio) in ('N/D', 'ND') then 'Não informado'
        else municipio
    end as nome,
    municipio as nome_fonte,
    case
        when municipio_ibge is null or upper(municipio) in ('N/D', 'ND') then 0
        else uf_ibge
    end as uf_ibge,
    uf_nome as uf_nome_fonte,
    case
        when municipio_ibge is null or upper(municipio) in ('N/D', 'ND') then cast(null as varchar)
        else sigla_regiao
    end as sigla_regiao,
    regiao_nome as regiao_nome_fonte,
    valor_pagador_pf,
    quantidade_pagador_pf,
    valor_pagador_pj,
    quantidade_pagador_pj,
    valor_recebedor_pf,
    quantidade_recebedor_pf,
    valor_recebedor_pj,
    quantidade_recebedor_pj,
    quantidade_pessoas_pagador_pf,
    quantidade_pessoas_pagador_pj,
    quantidade_pessoas_recebedor_pf,
    quantidade_pessoas_recebedor_pj
from staging.stg_transacoes_pix_municipio
