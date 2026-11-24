-- Latest CDC image of each operational PIX transaction, including deletes.

select
    op,
    lsn,
    lsn_ord,
    commit_ts,
    id,
    end_to_end_id,
    amount,
    payer_ispb,
    receiver_ispb,
    municipio_ibge,
    forma_iniciacao,
    direction,
    status,
    occurred_at,
    created_at,
    updated_at
from (
    select
        staged.*,
        row_number() over (
            partition by id
            order by lsn_ord desc
        ) as change_rank
    from {{ ref('stg_app_pix_transactions') }} as staged
) ranked
where change_rank = 1
