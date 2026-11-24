-- PIX value and counts by municipality and month, including the
-- "Não informado" member (municipio_ibge 0).
-- Grain: ano_mes, municipio_ibge.
-- valor_enviado is what payers in the municipality sent (PF + PJ).
-- valor_recebido is what receivers in the municipality got. Do not add
-- the two sides: a payment is counted once as sent and once as received,
-- often in different municipalities. quantidade_pessoas_* are distinct
-- people in that municipality-month. They are not additive across months,
-- and the sum across municipalities is not a national distinct count.

select
    ano_mes,
    municipio_ibge,
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
    quantidade_pessoas_recebedor_pj,
    valor_pagador_pf + valor_pagador_pj as valor_enviado,
    quantidade_pagador_pf + quantidade_pagador_pj as quantidade_enviada,
    valor_recebedor_pf + valor_recebedor_pj as valor_recebido,
    quantidade_recebedor_pf + quantidade_recebedor_pj as quantidade_recebida
from {{ ref('int_transacoes_municipio') }}
