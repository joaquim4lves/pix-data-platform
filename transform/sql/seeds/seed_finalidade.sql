-- FINALIDADE values published by Olinda (docs/spike-bcb.md).
-- The strings are already labels. Only "Nao disponivel" is accented here.

select
    codigo,
    rotulo,
    fonte
from (
    values
    ('Pix', 'Pix', 'olinda-texto'),
    ('Pix Saque', 'Pix Saque', 'olinda-texto'),
    ('Pix Troco', 'Pix Troco', 'olinda-texto'),
    ('Nao disponivel', 'Não disponível', 'olinda-texto')
) as finalidade(codigo, rotulo, fonte)
