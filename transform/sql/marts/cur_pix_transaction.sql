-- Current operational PIX transactions.
-- Grain: id. Deletes are removed. A refunded payment stays, with that status.
-- payer_ispb and receiver_ispb join to dim_instituicao.
-- municipio_ibge joins to dim_municipio. forma_iniciacao joins to
-- dim_forma_iniciacao.

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
    commit_ts
from intermediate.int_app_pix_transactions
where op <> 'delete'
