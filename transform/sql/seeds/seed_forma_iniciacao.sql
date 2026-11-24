-- FORMAINICIACAO codes from the 202610 extract (docs/spike-bcb.md).
-- DICT, MANU, INIC, QRES, QRDN, and AUTO are the "Tipo de Iniciação"
-- columns in Banco Central do Brasil, Manual de Padrões para Iniciação
-- do Pix, versão 2.10.0, seção 3.2.
-- APDN is the catalog domain for Pix por aproximação (Fórum Pix, 24ª
-- reunião plenária; Manual seção 3.4 describes the NFC flow).
-- APES is in the extract. The label treats it as the static counterpart
-- of APDN, parallel to QRES/QRDN. That gloss is not a BCB sentence, so
-- publicado is false.
-- "Nao disponivel" is the API's own text, not a manual code.

select
    codigo,
    rotulo,
    publicado,
    fonte
from (
    values
    ('DICT', 'Chave Pix', true, 'bcb-manual-iniciacao-pix-2.10'),
    ('MANU', 'Inserção manual dos dados', true, 'bcb-manual-iniciacao-pix-2.10'),
    ('INIC', 'Serviço de iniciação de transação de pagamento', true, 'bcb-manual-iniciacao-pix-2.10'),
    ('QRES', 'QR Code estático', true, 'bcb-manual-iniciacao-pix-2.10'),
    ('QRDN', 'QR Code dinâmico', true, 'bcb-manual-iniciacao-pix-2.10'),
    ('AUTO', 'Pix Automático', true, 'bcb-manual-iniciacao-pix-2.10'),
    ('APDN', 'Pix por aproximação', true, 'bcb-forum-pix-dominio-apdn'),
    ('APES', 'Pix por aproximação estático', false, 'inferido-par-qres-qrdn'),
    ('Nao disponivel', 'Não disponível', true, 'olinda-texto')
) as forma_iniciacao(codigo, rotulo, publicado, fonte)
