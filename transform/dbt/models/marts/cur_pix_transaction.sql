{% if target.type == 'duckdb' %}
{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='id',
    on_schema_change='sync_all_columns',
    post_hook="{{ cdc_drop_deletes('int_app_pix_transactions') }}",
) }}
{% else %}
{{ config(materialized='view') }}
{% endif %}

-- Current operational PIX transactions.
-- Grain: id. Deletes are removed. A refunded payment stays, with that status.
-- payer_ispb and receiver_ispb join to dim_instituicao.
-- municipio_ibge joins to dim_municipio. forma_iniciacao joins to
-- dim_forma_iniciacao.
--
-- Same LSN merge as cur_pix_key. commit_ts can go backwards relative to the
-- WAL (clock skew, a replay). lsn_ord does not. A late file with a smaller
-- LSN is ignored. A delete whose LSN wins is removed by the post-hook.

select
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
    updated_at,
    lsn,
    lsn_ord,
    commit_ts
from {{ ref('int_app_pix_transactions') }} as images
where op <> 'delete'
{% if is_incremental() %}
    and lsn_ord > (
        select coalesce(max(current_row.lsn_ord), '')
        from {{ this }} as current_row
        where current_row.id = images.id
    )
{% endif %}
