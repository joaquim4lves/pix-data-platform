select
    ano_mes,
    municipio_ibge
from marts.fct_transacoes_municipio
where valor_pagador_pf < 0
    or valor_pagador_pj < 0
    or valor_recebedor_pf < 0
    or valor_recebedor_pj < 0
    or quantidade_pagador_pf < 0
    or quantidade_pagador_pj < 0
    or quantidade_recebedor_pf < 0
    or quantidade_recebedor_pj < 0
    or quantidade_pessoas_pagador_pf < 0
    or quantidade_pessoas_pagador_pj < 0
    or quantidade_pessoas_recebedor_pf < 0
    or quantidade_pessoas_recebedor_pj < 0
    or valor_enviado < 0
    or valor_recebido < 0
    or quantidade_enviada < 0
    or quantidade_recebida < 0
