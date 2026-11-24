-- Age-band strings published by Olinda (docs/spike-bcb.md).
-- The rotulo is the API text. ordem is for charts, youngest first,
-- with the two non-age values last.

select
    codigo,
    rotulo,
    ordem,
    fonte
from (
    values
    ('até 19 anos', 'até 19 anos', 1, 'olinda-texto'),
    ('entre 20 e 29 anos', 'entre 20 e 29 anos', 2, 'olinda-texto'),
    ('entre 30 e 39 anos', 'entre 30 e 39 anos', 3, 'olinda-texto'),
    ('entre 40 e 49 anos', 'entre 40 e 49 anos', 4, 'olinda-texto'),
    ('entre 50 e 59 anos', 'entre 50 e 59 anos', 5, 'olinda-texto'),
    ('mais de 60 anos', 'mais de 60 anos', 6, 'olinda-texto'),
    ('Nao se aplica', 'Nao se aplica', 7, 'olinda-texto'),
    ('Nao informado', 'Nao informado', 8, 'olinda-texto')
) as faixa_idade(codigo, rotulo, ordem, fonte)
