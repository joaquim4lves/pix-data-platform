-- Stock of active PIX keys.
-- Grain: ano_mes, ispb, natureza_usuario, tipo_chave.
-- One row is the key count for that institution, person type, and key
-- type on the snapshot date (the last day of the month in the extract).
-- This is not a flow and not payment volume. Summing quantidade_chaves
-- across months recounts the same keys. Summing across key types on one
-- snapshot is the institution's key stock for that month.

select
    ano_mes,
    data_referencia,
    ispb,
    natureza_usuario,
    tipo_chave,
    quantidade_chaves
from intermediate.int_chaves_pix
