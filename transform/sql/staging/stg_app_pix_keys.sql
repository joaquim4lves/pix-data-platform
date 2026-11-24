-- CDC log for the operational PIX key registry.
-- The sink writes every column as text. Casts live here, same as the
-- Olinda staging models. commit_ts is UTC. lsn_ord is fixed-width hex so
-- the latest change follows the WAL rather than the clock.

select
    op,
    lsn,
    lsn_ord,
    cast(commit_ts as timestamp) as commit_ts,
    pk,
    id,
    key_type,
    key_value,
    person_type,
    lpad(ispb, 8, '0') as ispb,
    cast(municipio_ibge as integer) as municipio_ibge,
    status,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at
from raw.app_pix_keys
