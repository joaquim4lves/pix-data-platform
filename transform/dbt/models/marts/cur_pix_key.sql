{% if target.type == 'duckdb' %}
{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='id',
    on_schema_change='sync_all_columns',
    post_hook="{{ cdc_drop_deletes('int_app_pix_keys') }}",
) }}
{% else %}
{{ config(materialized='view') }}
{% endif %}

-- Current PIX key registry.
-- Grain: id. The latest CDC image, with deletes removed.
-- ispb joins to dim_instituicao. municipio_ibge joins to dim_municipio.
-- lsn is the commit that produced this image, not a business timestamp.
--
-- Incremental strategy (DuckDB): delete+insert on id. Ordering is lsn_ord,
-- the fixed-width hex of the commit LSN, not file arrival and not commit_ts.
-- A late Parquet file is applied only when its winning lsn_ord is greater
-- than the lsn_ord already stored for that id. An older LSN in a file that
-- lands after a newer one does not replace the row. When the winning op is
-- delete, the select omits the id and the post-hook removes it. The first
-- build is a full refresh and matches the legacy mart, plus lsn_ord, which
-- the merge needs on the next run. Athena keeps this as a view: the v0.4
-- catalog is Hive Parquet, not Iceberg, so there is no merge table there.

select
    id,
    key_type,
    key_value,
    person_type,
    ispb,
    municipio_ibge,
    status,
    created_at,
    updated_at,
    lsn,
    lsn_ord,
    commit_ts
from {{ ref('int_app_pix_keys') }} as images
where op <> 'delete'
{% if is_incremental() %}
    and lsn_ord > (
        select coalesce(max(current_row.lsn_ord), '')
        from {{ this }} as current_row
        where current_row.id = images.id
    )
{% endif %}
