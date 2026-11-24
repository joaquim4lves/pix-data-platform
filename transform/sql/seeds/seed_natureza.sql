-- Nine NATUREZA codes observed in the full 202610 extract
-- (docs/spike-bcb.md). First letter is the payer, second is the receiver:
-- P pessoa física, B pessoa jurídica, G governo.
--
-- P2P, P2B, B2P, and B2B are the footnote in Banco Central do Brasil,
-- Relatório Anual do SPI 2025.
-- P2G is named in Relatório de Gestão do Pix 2023-2025
-- ("person to government"; the report spells government with a typo).
-- G2P, B2G, G2B, and G2G use that same convention. The Gestão report
-- groups those flows as Governo and does not publish a separate gloss,
-- so publicado is false for them.

select
    codigo,
    rotulo,
    descricao,
    publicado,
    fonte
from (
    values
    (
        'P2P',
        'Pessoa física para pessoa física',
        'Pagador pessoa física, recebedor pessoa física',
        true,
        'bcb-relatorio-anual-spi-2025'
    ),
    (
        'P2B',
        'Pessoa física para pessoa jurídica',
        'Pagador pessoa física, recebedor pessoa jurídica',
        true,
        'bcb-relatorio-anual-spi-2025'
    ),
    (
        'B2P',
        'Pessoa jurídica para pessoa física',
        'Pagador pessoa jurídica, recebedor pessoa física',
        true,
        'bcb-relatorio-anual-spi-2025'
    ),
    (
        'B2B',
        'Pessoa jurídica para pessoa jurídica',
        'Pagador pessoa jurídica, recebedor pessoa jurídica',
        true,
        'bcb-relatorio-anual-spi-2025'
    ),
    (
        'P2G',
        'Pessoa física para o governo',
        'Pagador pessoa física, recebedor governo',
        true,
        'bcb-relatorio-gestao-pix-2023-2025'
    ),
    (
        'G2P',
        'Governo para pessoa física',
        'Pagador governo, recebedor pessoa física',
        false,
        'convencao-pbg'
    ),
    (
        'B2G',
        'Pessoa jurídica para o governo',
        'Pagador pessoa jurídica, recebedor governo',
        false,
        'convencao-pbg'
    ),
    (
        'G2B',
        'Governo para pessoa jurídica',
        'Pagador governo, recebedor pessoa jurídica',
        false,
        'convencao-pbg'
    ),
    (
        'G2G',
        'Governo para governo',
        'Pagador governo, recebedor governo',
        false,
        'convencao-pbg'
    )
) as natureza(codigo, rotulo, descricao, publicado, fonte)
