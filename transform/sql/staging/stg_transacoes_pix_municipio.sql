-- Typed, renamed projection of TransacoesPixPorMunicipio.
-- Null IBGE codes are preserved. The N/D bucket is labeled downstream
-- and is not dropped here.

select
    cast("AnoMes" as integer) as ano_mes,
    cast("Municipio_Ibge" as integer) as municipio_ibge,
    trim("Municipio") as municipio,
    cast("Estado_Ibge" as integer) as uf_ibge,
    trim("Estado") as uf_nome,
    trim("Sigla_Regiao") as sigla_regiao,
    trim("Regiao") as regiao_nome,
    cast("VL_PagadorPF" as decimal(38, 8)) as valor_pagador_pf,
    cast("QT_PagadorPF" as decimal(38, 8)) as quantidade_pagador_pf,
    cast("VL_PagadorPJ" as decimal(38, 8)) as valor_pagador_pj,
    cast("QT_PagadorPJ" as decimal(38, 8)) as quantidade_pagador_pj,
    cast("VL_RecebedorPF" as decimal(38, 8)) as valor_recebedor_pf,
    cast("QT_RecebedorPF" as decimal(38, 8)) as quantidade_recebedor_pf,
    cast("VL_RecebedorPJ" as decimal(38, 8)) as valor_recebedor_pj,
    cast("QT_RecebedorPJ" as decimal(38, 8)) as quantidade_recebedor_pj,
    cast("QT_PES_PagadorPF" as decimal(38, 8)) as quantidade_pessoas_pagador_pf,
    cast("QT_PES_PagadorPJ" as decimal(38, 8)) as quantidade_pessoas_pagador_pj,
    cast("QT_PES_RecebedorPF" as decimal(38, 8)) as quantidade_pessoas_recebedor_pf,
    cast("QT_PES_RecebedorPJ" as decimal(38, 8)) as quantidade_pessoas_recebedor_pj
from raw.transacoes_pix_municipio
