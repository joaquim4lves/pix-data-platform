-- Typed CnaePorteRecebedor. mesmatit, vlcompra and vldinespec are
-- staged so a later slice can use them. The v1.0 mart does not select
-- them. formainic here is not the FORMAINICIACAO vocabulary.

select
    cast("AnoMes" as integer) as ano_mes,
    trim("tipopessoa") as tipo_pessoa,
    trim("formainic") as forma_iniciacao,
    trim("finalidade") as finalidade,
    trim("porte") as porte,
    trim("mei") as mei,
    trim("cnssecao") as cnae_secao,
    trim("mesmatit") as mesmo_titular,
    trim("naturezarel") as natureza,
    cast("qtpagador" as decimal(38, 8)) as quantidade_pagador,
    cast("qtrecebedor" as decimal(38, 8)) as quantidade_recebedor,
    cast("qtlanliq" as decimal(38, 8)) as quantidade_liquidada,
    cast("vllanliq" as decimal(38, 8)) as valor_liquidado,
    cast("vlcompra" as decimal(38, 8)) as valor_compra,
    cast("vldinespec" as decimal(38, 8)) as valor_dinheiro_especie
from {{ source('raw', 'cnae_porte_recebedor') }}
where "AnoMes" is not null
