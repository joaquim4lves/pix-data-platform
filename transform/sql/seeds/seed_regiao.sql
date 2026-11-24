-- Macro-regions as EstatisticasTransacoesPix spells them, plus the
-- published "Nao informado" value. Siglas match TransacoesPixPorMunicipio
-- and the IBGE five-region division.

select
    codigo,
    rotulo,
    sigla,
    fonte
from (
    values
    ('NORTE', 'Norte', 'N', 'ibge-grandes-regioes'),
    ('NORDESTE', 'Nordeste', 'NE', 'ibge-grandes-regioes'),
    ('SUDESTE', 'Sudeste', 'SE', 'ibge-grandes-regioes'),
    ('SUL', 'Sul', 'S', 'ibge-grandes-regioes'),
    ('CENTRO-OESTE', 'Centro-Oeste', 'CO', 'ibge-grandes-regioes'),
    ('Nao informado', 'Não informado', cast(null as varchar), 'olinda-texto')
) as regiao(codigo, rotulo, sigla, fonte)
