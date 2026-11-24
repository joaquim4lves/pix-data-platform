-- Current simulated MED disputes.
-- Grain: id. An accepted or rejected dispute stays until it is deleted.
-- transaction_id points at cur_pix_transaction. A dispute whose payment
-- was deleted fails the referential check on purpose.

select
    id,
    transaction_id,
    reason,
    status,
    opened_at,
    resolved_at,
    created_at,
    updated_at,
    lsn,
    commit_ts
from intermediate.int_app_pix_disputes
where op <> 'delete'
