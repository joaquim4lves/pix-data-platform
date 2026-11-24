-- Latest CDC image of each PIX key, including deletes.
-- The consumer already collapses a transaction to one event per id.
-- Two commits for the same id are ordered by lsn_ord, not by file order
-- and not by commit_ts.

select
    op,
    lsn,
    lsn_ord,
    commit_ts,
    id,
    key_type,
    key_value,
    person_type,
    ispb,
    municipio_ibge,
    status,
    created_at,
    updated_at
from (
    select
        staged.*,
        row_number() over (
            partition by id
            order by lsn_ord desc
        ) as change_rank
    from {{ ref('stg_app_pix_keys') }} as staged
) ranked
where change_rank = 1
