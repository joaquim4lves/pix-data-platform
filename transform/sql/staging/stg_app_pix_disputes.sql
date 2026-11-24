-- CDC log for simulated MED disputes opened against an operational transaction.
-- resolved_at is null while the dispute is open.

select
    op,
    lsn,
    lsn_ord,
    cast(commit_ts as timestamp) as commit_ts,
    pk,
    id,
    transaction_id,
    reason,
    status,
    cast(opened_at as timestamp) as opened_at,
    cast(resolved_at as timestamp) as resolved_at,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at
from raw.app_pix_disputes
