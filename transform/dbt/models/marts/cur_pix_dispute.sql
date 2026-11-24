{% if target.type == 'duckdb' %}
{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='id',
    on_schema_change='sync_all_columns',
    post_hook="{{ cdc_drop_deletes('int_app_pix_disputes') }}",
) }}
{% else %}
{{ config(materialized='view') }}
{% endif %}

-- Current simulated MED disputes.
-- Grain: id. An accepted or rejected dispute stays until it is deleted.
-- transaction_id points at cur_pix_transaction. A dispute whose payment
-- was deleted fails the referential check on purpose.
--
-- Same LSN merge as cur_pix_key. The intermediate model ranks the whole
-- log, so a partition that arrives late is still visible. The incremental
-- predicate keeps the stored image unless the new winner has a greater
-- lsn_ord.

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
    lsn_ord,
    commit_ts
from {{ ref('int_app_pix_disputes') }} as images
where op <> 'delete'
{% if is_incremental() %}
    and lsn_ord > (
        select coalesce(max(current_row.lsn_ord), '')
        from {{ this }} as current_row
        where current_row.id = images.id
    )
{% endif %}
