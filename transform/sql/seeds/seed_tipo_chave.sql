-- TipoChave values in the ChavesPix snapshot of 2026-10-31
-- (docs/spike-bcb.md). The API already returns readable labels.
-- ordem is a stable chart order, not a volume ranking.

select
    codigo,
    rotulo,
    ordem,
    fonte
from (
    values
    ('CPF', 'CPF', 1, 'olinda-chavespix'),
    ('CNPJ', 'CNPJ', 2, 'olinda-chavespix'),
    ('Celular', 'Celular', 3, 'olinda-chavespix'),
    ('e-mail', 'E-mail', 4, 'olinda-chavespix'),
    ('Aleatória', 'Aleatória', 5, 'olinda-chavespix')
) as tipo_chave(codigo, rotulo, ordem, fonte)
