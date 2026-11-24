-- IBGE state codes (UF) and the five macro-regions.
-- uf_ibge 0 is the sentinel for the PIX "Não informado" bucket. IBGE
-- does not assign 0 to a state. Source: IBGE, códigos das unidades da
-- federação and the divisão regional do Brasil.

select
    uf_ibge,
    sigla,
    nome,
    sigla_regiao,
    regiao_nome
from (
    values
    (11, 'RO', 'Rondônia', 'N', 'Norte'),
    (12, 'AC', 'Acre', 'N', 'Norte'),
    (13, 'AM', 'Amazonas', 'N', 'Norte'),
    (14, 'RR', 'Roraima', 'N', 'Norte'),
    (15, 'PA', 'Pará', 'N', 'Norte'),
    (16, 'AP', 'Amapá', 'N', 'Norte'),
    (17, 'TO', 'Tocantins', 'N', 'Norte'),
    (21, 'MA', 'Maranhão', 'NE', 'Nordeste'),
    (22, 'PI', 'Piauí', 'NE', 'Nordeste'),
    (23, 'CE', 'Ceará', 'NE', 'Nordeste'),
    (24, 'RN', 'Rio Grande do Norte', 'NE', 'Nordeste'),
    (25, 'PB', 'Paraíba', 'NE', 'Nordeste'),
    (26, 'PE', 'Pernambuco', 'NE', 'Nordeste'),
    (27, 'AL', 'Alagoas', 'NE', 'Nordeste'),
    (28, 'SE', 'Sergipe', 'NE', 'Nordeste'),
    (29, 'BA', 'Bahia', 'NE', 'Nordeste'),
    (31, 'MG', 'Minas Gerais', 'SE', 'Sudeste'),
    (32, 'ES', 'Espírito Santo', 'SE', 'Sudeste'),
    (33, 'RJ', 'Rio de Janeiro', 'SE', 'Sudeste'),
    (35, 'SP', 'São Paulo', 'SE', 'Sudeste'),
    (41, 'PR', 'Paraná', 'S', 'Sul'),
    (42, 'SC', 'Santa Catarina', 'S', 'Sul'),
    (43, 'RS', 'Rio Grande do Sul', 'S', 'Sul'),
    (50, 'MS', 'Mato Grosso do Sul', 'CO', 'Centro-Oeste'),
    (51, 'MT', 'Mato Grosso', 'CO', 'Centro-Oeste'),
    (52, 'GO', 'Goiás', 'CO', 'Centro-Oeste'),
    (53, 'DF', 'Distrito Federal', 'CO', 'Centro-Oeste'),
    (0, cast(null as varchar), 'Não informado', cast(null as varchar), 'Não informado')
) as uf(uf_ibge, sigla, nome, sigla_regiao, regiao_nome)
