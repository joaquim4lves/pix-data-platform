-- A dispute that outlived its payment is a broken merge, not an open case.

select
    dispute.id as dispute_id,
    dispute.transaction_id
from marts.cur_pix_dispute as dispute
left join marts.cur_pix_transaction as payment
    on dispute.transaction_id = payment.id
where payment.id is null
