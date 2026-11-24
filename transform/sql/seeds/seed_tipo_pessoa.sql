-- PAG_PFPJ, REC_PFPJ, and NaturezaUsuario.
-- PF and PJ are the values in the extract (docs/spike-bcb.md).

select
    codigo,
    rotulo,
    fonte
from (
    values
    ('PF', 'Pessoa física', 'olinda-texto'),
    ('PJ', 'Pessoa jurídica', 'olinda-texto')
) as tipo_pessoa(codigo, rotulo, fonte)
