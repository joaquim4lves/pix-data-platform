-- Current PIX key registry.
-- Grain: id. The latest CDC image, with deletes removed.
-- ispb joins to dim_instituicao. municipio_ibge joins to dim_municipio.
-- lsn is the commit that produced this image, not a business timestamp.

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
    commit_ts
from intermediate.int_app_pix_keys
where op <> 'delete'
