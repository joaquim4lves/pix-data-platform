"""Row builders that match the live Olinda shapes used by the contracts."""


def tx_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "AnoMes": 202610,
        "PAG_PFPJ": "PJ",
        "REC_PFPJ": "PF",
        "PAG_REGIAO": "NORDESTE",
        "REC_REGIAO": "SUL",
        "PAG_IDADE": "Nao se aplica",
        "REC_IDADE": "mais de 60 anos",
        "FORMAINICIACAO": "Nao disponivel",
        "NATUREZA": "B2P",
        "FINALIDADE": "Pix",
        "VALOR": "686701.07",
        "QUANTIDADE": 777,
    }
    row.update(overrides)
    return row


def municipio_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "AnoMes": 202610,
        "Municipio_Ibge": 2103406,
        "Municipio": "COELHO NETO",
        "Estado_Ibge": 21,
        "Estado": "MARANHÃO",
        "Sigla_Regiao": "NE",
        "Regiao": "NORDESTE",
        "VL_PagadorPF": "142493207.35",
        "QT_PagadorPF": 1404865,
        "VL_PagadorPJ": "21736052.65",
        "QT_PagadorPJ": 42643,
        "VL_RecebedorPF": "127717854.01",
        "QT_RecebedorPF": 840042,
        "VL_RecebedorPJ": "27402102.28",
        "QT_RecebedorPJ": 201057,
        "QT_PES_PagadorPF": 28561,
        "QT_PES_PagadorPJ": 702,
        "QT_PES_RecebedorPF": 27542,
        "QT_PES_RecebedorPJ": 677,
    }
    row.update(overrides)
    return row


def fraud_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "AnoMes": 202609,
        "QtdePixcontestados": "1000",
        "Qtdecontestacoesaceitas": "400",
        "Qtdecontestacoesrejeitadas": "600",
        "Qtdecontestacoesaceitasacada100mil": "3.834",
        "QtdeUsuarioscommarcacoesdefraude": "120",
        "QtdeChavesPixcommarcacoesdefraude": "80",
        "ValorPixcontestadosaceitos": "250.00",
        "QuantidadedevolvidaintegralmentepormeiodoMED": "200",
        "ValorPixdevolvidosintegralmente": "140.00",
        "QuantidadedevolvidaparcialmentepormeiodoMED": "40",
        "ValorPixdevolvidosparcialmente": "20.00",
        "ValorPixresidualnaodevolvido": "90.00",
        "Quantidadedenaodevolvidossaldoinsuficiente": "70",
        "ValorPixnaodevolvidossaldoinsuficiente": "40.00",
        "Quantidadedenaodevolvidoscontaencerrada": "20",
        "Valornaodevolvidoscontaencerrada": "15.00",
        "Quantidadedenaodevolvidosmotivosdiversos": "30",
        "ValorPixnaodevolvidosmotivosdiversos": "35.00",
        "PercentualdeDevolucao": "40.0",
        "QtdePixbloqueadoscautelarmenteeliberados": "1",
        "ValorPixbloqueadoscautelarmenteeliberados": "2.00",
        "QtdePixbloqueadoscautelarmenteedevolvidos": "3",
        "ValorPixbloqueadoscautelarmenteedevolvidos": "4.00",
    }
    row.update(overrides)
    return row


def cnae_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "AnoMes": 202610,
        "tipopessoa": "PJ",
        "formainic": "DICT",
        "finalidade": "Pix",
        "porte": "Microempresa",
        "mei": "S",
        "cnssecao": "G - Comercio",
        "mesmatit": "N",
        "naturezarel": "P2B",
        "qtpagador": "10",
        "qtrecebedor": "8",
        "qtlanliq": "20",
        "vllanliq": "1000.00",
        "vlcompra": "1.00",
        "vldinespec": "2.00",
    }
    row.update(overrides)
    return row


def dict_users_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "DataGraficosPix": "2026-10-31",
        "qtdUsuariosPessoaFisica": 100,
        "qtdUsuariosPessoaJuridica": 25,
        "qtdUsuariosCadastradosDICTTotal": 125,
    }
    row.update(overrides)
    return row


def chaves_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "Data": "2026-10-31",
        "ISPB": "05938780",
        "Nome": "COOPER CARD IP",
        "NaturezaUsuario": "PF",
        "TipoChave": "CPF",
        "qtdChaves": 917,
        "Segmento": "Instituição de Pagamento",
    }
    row.update(overrides)
    return row
