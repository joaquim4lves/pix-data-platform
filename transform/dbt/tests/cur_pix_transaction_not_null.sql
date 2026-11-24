-- A current transaction keeps the codes the warehouse dimensions use.

select
    id
from {{ ref('cur_pix_transaction') }}
where id is null
    or end_to_end_id is null
    or amount is null
    or payer_ispb is null
    or length(payer_ispb) <> 8
    or receiver_ispb is null
    or length(receiver_ispb) <> 8
    or municipio_ibge is null
    or forma_iniciacao is null
    or direction is null
    or status is null
