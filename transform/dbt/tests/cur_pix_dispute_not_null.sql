-- A current dispute names a payment, a reason, and a status.

select
    id
from {{ ref('cur_pix_dispute') }}
where id is null
    or transaction_id is null
    or reason is null
    or status is null
    or opened_at is null
