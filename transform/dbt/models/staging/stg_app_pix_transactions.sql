-- CDC log for operational PIX transactions.
-- amount is the text pgoutput emitted (for example 10.50). direction is
-- inbound or outbound from the simulated PSP's point of view.

select
    op,
    lsn,
    lsn_ord,
    cast(commit_ts as timestamp) as commit_ts,
    pk,
    id,
    end_to_end_id,
    cast(amount as decimal(18, 2)) as amount,
    lpad(payer_ispb, 8, '0') as payer_ispb,
    lpad(receiver_ispb, 8, '0') as receiver_ispb,
    cast(municipio_ibge as integer) as municipio_ibge,
    forma_iniciacao,
    direction,
    status,
    cast(occurred_at as timestamp) as occurred_at,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at
from {{ source('raw', 'app_pix_transactions') }}
