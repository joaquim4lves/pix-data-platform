-- Latest CDC image of each dispute, including deletes.

select
    op,
    lsn,
    lsn_ord,
    commit_ts,
    id,
    transaction_id,
    reason,
    status,
    opened_at,
    resolved_at,
    created_at,
    updated_at
from (
    select
        staged.*,
        row_number() over (
            partition by id
            order by lsn_ord desc
        ) as change_rank
    from staging.stg_app_pix_disputes as staged
) ranked
where change_rank = 1
