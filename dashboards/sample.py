"""Seeded Olinda-shaped Parquet for the local dashboards.

The files follow the v1.0 contracts. They are not a download from BCB.
National totals, municipality rows, and institution names are synthetic.
202610 DICT user counts match the figures recorded in docs/spike-bcb.md so
the KPI is recognisable. MED stops at 202609. 202611 is a partial month
and is flagged incomplete when the as-of date is 2026-11-25.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
from ingestion.bcb.entities import (
    CHAVES,
    CNAE,
    FRAUDES,
    MUNICIPIO,
    TRANSACOES,
    USUARIOS,
    EntitySpec,
)
from ingestion.bcb.store import _table

NATUREZA = ("P2P", "P2B", "B2P", "B2B", "P2G", "G2P", "G2B", "B2G", "G2G")
NATUREZA_WEIGHT = {
    "P2P": 0.46,
    "P2B": 0.27,
    "B2P": 0.08,
    "B2B": 0.11,
    "P2G": 0.03,
    "G2P": 0.025,
    "G2B": 0.012,
    "B2G": 0.008,
    "G2G": 0.005,
}
FORMAS = ("DICT", "QRDN", "QRES", "MANU", "INIC", "AUTO", "APDN", "APES", "Nao disponivel")
REGIONS = ("NORTE", "NORDESTE", "CENTRO-OESTE", "SUDESTE", "SUL", "Nao informado")
AGES = (
    "até 19 anos",
    "entre 20 e 29 anos",
    "entre 30 e 39 anos",
    "entre 40 e 49 anos",
    "entre 50 e 59 anos",
    "mais de 60 anos",
    "Nao informado",
)
CITIES = (
    (3550308, "SAO PAULO", 35, "SAO PAULO", "SE", "SUDESTE", 1.00),
    (3304557, "RIO DE JANEIRO", 33, "RIO DE JANEIRO", "SE", "SUDESTE", 0.62),
    (3106200, "BELO HORIZONTE", 31, "MINAS GERAIS", "SE", "SUDESTE", 0.41),
    (4106902, "CURITIBA", 41, "PARANA", "S", "SUL", 0.33),
    (4314902, "PORTO ALEGRE", 43, "RIO GRANDE DO SUL", "S", "SUL", 0.29),
    (2927408, "SALVADOR", 29, "BAHIA", "NE", "NORDESTE", 0.36),
    (2611606, "RECIFE", 26, "PERNAMBUCO", "NE", "NORDESTE", 0.24),
    (2304400, "FORTALEZA", 23, "CEARA", "NE", "NORDESTE", 0.27),
    (1302603, "MANAUS", 13, "AMAZONAS", "N", "NORTE", 0.18),
    (5300108, "BRASILIA", 53, "DISTRITO FEDERAL", "CO", "CENTRO-OESTE", 0.31),
    (5208707, "GOIANIA", 52, "GOIAS", "CO", "CENTRO-OESTE", 0.16),
)
BANKS = (
    ("00000001", "Atlântica IP", "Instituição de Pagamento", 1.00),
    ("00000002", "Serra Credit Union", "Cooperativa de Crédito", 0.62),
    ("00000003", "Norte Bank", "Banco Múltiplo", 0.84),
    ("00000004", "Litoral SCD", "Sociedade de Crédito Direto", 0.28),
    ("00000005", "Cerrado Cooperative", "Cooperativa de Crédito", 0.47),
    ("00000006", "Pampa Payments", "Instituição de Pagamento", 0.55),
)
SECTIONS = (
    ("G - Comercio", 0.22),
    ("C - Industrias de transformacao", 0.14),
    ("K - Atividades financeiras", 0.11),
    ("Q - Saude", 0.09),
    ("P - Educacao", 0.06),
    ("I - Alojamento e alimentacao", 0.08),
    ("R - Artes, cultura, esporte e recreacao", 0.05),
    ("M - Atividades profissionais", 0.07),
    ("Pessoa fisica", 0.12),
    ("Outros", 0.06),
)
PORTES = (
    ("Microempresa", 0.34),
    ("Pequeno Porte", 0.22),
    ("Media Empresa", 0.18),
    ("Grande", 0.26),
)
KEY_TYPES = ("CPF", "CNPJ", "Celular", "e-mail", "Aleatória")


def months(start: int, end: int) -> list[int]:
    year, month = divmod(start, 100)
    end_year, end_month = divmod(end, 100)
    found: list[int] = []
    while (year, month) <= (end_year, end_month):
        found.append(year * 100 + month)
        month += 1
        if month == 13:
            month = 1
            year += 1
    return found


def month_index(ano_mes: int) -> int:
    year, month = divmod(ano_mes, 100)
    return (year - 2022) * 12 + (month - 1)


def _money(value: float) -> str:
    return f"{value:.2f}"


def _write(root: Path, spec: EntitySpec, ano_mes: int, rows: list[dict[str, object]]) -> None:
    models = [spec.model.model_validate(row) for row in rows]
    table = _table(spec, models)
    path = root / "bcb" / spec.name / f"ano_mes={ano_mes}" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, compression="snappy")


def _forma_weight(forma: str, index: int) -> float:
    growth = min(index, 57) / 57
    base = {
        "DICT": 0.34 + 0.16 * growth,
        "QRDN": 0.16 + 0.06 * growth,
        "QRES": 0.12,
        "MANU": 0.11 - 0.04 * growth,
        "INIC": 0.08,
        "AUTO": 0.03 + 0.07 * growth,
        "APDN": 0.025,
        "APES": 0.015,
        "Nao disponivel": 0.12 - 0.05 * growth,
    }
    total = sum(base.values())
    return base[forma] / total


def _ticket(natureza: str) -> float:
    return {
        "P2P": 180,
        "P2B": 240,
        "B2P": 310,
        "B2B": 4200,
        "P2G": 260,
        "G2P": 890,
        "G2B": 5400,
        "B2G": 6100,
        "G2G": 7200,
    }[natureza]


def _transactions(ano_mes: int, partial: bool) -> list[dict[str, object]]:
    index = month_index(ano_mes)
    national = 820_000_000_000 + index * 14_500_000_000
    if partial:
        national *= 0.42
    rows: list[dict[str, object]] = []
    naturezas = NATUREZA[:4] if partial else NATUREZA
    for i, natureza in enumerate(naturezas):
        payer_pf = natureza[0] == "P"
        receiver_pf = natureza[2] == "P"
        for j, forma in enumerate(FORMAS):
            if partial and j % 2:
                continue
            valor = national * NATUREZA_WEIGHT[natureza] * _forma_weight(forma, index)
            quantidade = max(valor / _ticket(natureza), 1)
            finalidade = "Pix"
            if j % 11 == 0:
                finalidade = "Pix Saque"
            elif j % 11 == 1:
                finalidade = "Pix Troco"
            elif j % 17 == 0:
                finalidade = "Nao disponivel"
            rows.append(
                {
                    "AnoMes": ano_mes,
                    "PAG_PFPJ": "PF" if payer_pf else "PJ",
                    "REC_PFPJ": "PF" if receiver_pf else "PJ",
                    "PAG_REGIAO": REGIONS[(i + j) % len(REGIONS)],
                    "REC_REGIAO": REGIONS[(i + 2 * j + 1) % len(REGIONS)],
                    "PAG_IDADE": AGES[(i + j) % len(AGES)] if payer_pf else "Nao se aplica",
                    "REC_IDADE": AGES[(i + 3) % len(AGES)] if receiver_pf else "Nao se aplica",
                    "FORMAINICIACAO": forma,
                    "NATUREZA": natureza,
                    "FINALIDADE": finalidade,
                    "VALOR": _money(valor),
                    "QUANTIDADE": str(int(quantidade)),
                }
            )
    return rows


def _municipalities(ano_mes: int, partial: bool) -> list[dict[str, object]]:
    index = max(month_index(ano_mes), 0)
    scale = (0.55 if partial else 1) * (1 + index * 0.012)
    rows: list[dict[str, object]] = []
    for code, name, uf, estado, sigla, regiao, weight in CITIES:
        base = 8_500_000_000 * weight * scale
        rows.append(
            {
                "AnoMes": ano_mes,
                "Municipio_Ibge": code,
                "Municipio": name,
                "Estado_Ibge": uf,
                "Estado": estado,
                "Sigla_Regiao": sigla,
                "Regiao": regiao,
                "VL_PagadorPF": _money(base * 0.62),
                "QT_PagadorPF": str(int(base * 0.62 / 190)),
                "VL_PagadorPJ": _money(base * 0.38),
                "QT_PagadorPJ": str(int(base * 0.38 / 2400)),
                "VL_RecebedorPF": _money(base * 0.57),
                "QT_RecebedorPF": str(int(base * 0.57 / 175)),
                "VL_RecebedorPJ": _money(base * 0.43),
                "QT_RecebedorPJ": str(int(base * 0.43 / 2100)),
                "QT_PES_PagadorPF": str(int(base * 0.62 / 190 / 18)),
                "QT_PES_PagadorPJ": str(int(base * 0.38 / 2400 / 6)),
                "QT_PES_RecebedorPF": str(int(base * 0.57 / 175 / 16)),
                "QT_PES_RecebedorPJ": str(int(base * 0.43 / 2100 / 5)),
            }
        )
    rows.append(
        {
            "AnoMes": ano_mes,
            "Municipio_Ibge": None,
            "Municipio": "N/D",
            "Estado_Ibge": None,
            "Estado": "NAO INFORMADO",
            "Sigla_Regiao": None,
            "Regiao": "Nao informado",
            "VL_PagadorPF": _money(400_000_000 * scale),
            "QT_PagadorPF": str(int(2_000_000 * scale)),
            "VL_PagadorPJ": _money(120_000_000 * scale),
            "QT_PagadorPJ": str(int(40_000 * scale)),
            "VL_RecebedorPF": _money(380_000_000 * scale),
            "QT_RecebedorPF": str(int(1_800_000 * scale)),
            "VL_RecebedorPJ": _money(90_000_000 * scale),
            "QT_RecebedorPJ": str(int(30_000 * scale)),
            "QT_PES_PagadorPF": str(int(90_000 * scale)),
            "QT_PES_PagadorPJ": str(int(4_000 * scale)),
            "QT_PES_RecebedorPF": str(int(80_000 * scale)),
            "QT_PES_RecebedorPJ": str(int(3_000 * scale)),
        }
    )
    return rows


def _keys(ano_mes: int) -> list[dict[str, object]]:
    year, month = divmod(ano_mes, 100)
    day = (
        29
        if month == 2 and year % 4 == 0
        else 28
        if month == 2
        else 30
        if month in (4, 6, 9, 11)
        else 31
    )
    data = f"{year:04d}-{month:02d}-{day:02d}"
    index = max(month_index(ano_mes), 0)
    rows: list[dict[str, object]] = []
    mix = {"CPF": 0.42, "Celular": 0.27, "Aleatória": 0.16, "e-mail": 0.09, "CNPJ": 0.06}
    for ispb, nome, segmento, weight in BANKS:
        stock = int((2_400_000 + index * 35_000) * weight)
        for tipo in KEY_TYPES:
            share = mix[tipo]
            rows.append(
                {
                    "Data": data,
                    "ISPB": ispb,
                    "Nome": nome,
                    "NaturezaUsuario": "PJ" if tipo == "CNPJ" else "PF",
                    "TipoChave": tipo,
                    "qtdChaves": max(int(stock * share), 1),
                    "Segmento": segmento,
                }
            )
    return rows


def _dict_users(ano_mes: int) -> list[dict[str, object]]:
    year, month = divmod(ano_mes, 100)
    day = (
        29
        if month == 2 and year % 4 == 0
        else 28
        if month == 2
        else 30
        if month in (4, 6, 9, 11)
        else 31
    )
    # 202610 matches the spike. Earlier months step back. 202611 is partial and larger.
    if ano_mes == 202610:
        pf, pj = 168_816_010, 18_969_680
    elif ano_mes == 202611:
        pf, pj = 170_200_000, 19_100_000
    else:
        span = month_index(202610) or 1
        progress = month_index(ano_mes) / span
        pf = int(95_000_000 + (168_816_010 - 95_000_000) * progress)
        pj = int(8_500_000 + (18_969_680 - 8_500_000) * progress)
    return [
        {
            "DataGraficosPix": f"{year:04d}-{month:02d}-{day:02d}",
            "qtdUsuariosPessoaFisica": pf,
            "qtdUsuariosPessoaJuridica": pj,
            "qtdUsuariosCadastradosDICTTotal": pf + pj,
        }
    ]


def _cnae(ano_mes: int) -> list[dict[str, object]]:
    index = max(month_index(ano_mes), 0)
    total = 640_000_000_000 + index * 9_000_000_000
    rows: list[dict[str, object]] = []
    for section, section_weight in SECTIONS:
        person = "PF" if section == "Pessoa fisica" else "PJ"
        portes = (("Nao informado", 1.0),) if person == "PF" else PORTES
        meis = ("Outros",) if person == "PF" else ("S", "N", "Outros")
        for porte, porte_weight in portes:
            for mei in meis:
                mei_weight = {"S": 0.46, "N": 0.42, "Outros": 0.12}[mei]
                valor = total * section_weight * porte_weight * mei_weight
                ticket = 95 if person == "PF" else 1400 if porte == "Grande" else 220
                rows.append(
                    {
                        "AnoMes": ano_mes,
                        "tipopessoa": person,
                        "formainic": "DICT",
                        "finalidade": "Pix",
                        "porte": porte,
                        "mei": mei,
                        "cnssecao": section,
                        "mesmatit": "N",
                        "naturezarel": "P2P" if person == "PF" else "P2B",
                        "qtpagador": _money(valor / ticket / 2),
                        "qtrecebedor": _money(valor / ticket / 3),
                        "qtlanliq": _money(valor / ticket),
                        "vllanliq": _money(valor),
                        "vlcompra": "0",
                        "vldinespec": "0",
                    }
                )
    return rows


def _fraud_measures(ano_mes: int) -> dict[str, object]:
    index = month_index(ano_mes)
    end_index = month_index(202609)
    progress = index / end_index if end_index else 1
    contested = int(900_000 + (3_747_045 - 900_000) * progress)
    accepted = int(contested * (0.58 + 0.04 * progress))
    rejected = contested - accepted
    full = int(accepted * 0.61)
    partial = int(accepted * 0.14)
    saldo = int(accepted * 0.12)
    closed = int(accepted * 0.05)
    other = accepted - full - partial - saldo - closed
    valor_aceito = contested * (210 + index)
    return {
        "AnoMes": ano_mes,
        "QtdePixcontestados": str(contested),
        "Qtdecontestacoesaceitas": str(accepted),
        "Qtdecontestacoesrejeitadas": str(rejected),
        "Qtdecontestacoesaceitasacada100mil": f"{2.1 + 1.734 * progress:.3f}",
        "QtdeUsuarioscommarcacoesdefraude": str(80_000 + index * 4_200),
        "QtdeChavesPixcommarcacoesdefraude": str(40_000 + index * 2_100),
        "ValorPixcontestadosaceitos": _money(valor_aceito),
        "QuantidadedevolvidaintegralmentepormeiodoMED": str(full),
        "ValorPixdevolvidosintegralmente": _money(valor_aceito * 0.55),
        "QuantidadedevolvidaparcialmentepormeiodoMED": str(partial),
        "ValorPixdevolvidosparcialmente": _money(valor_aceito * 0.08),
        "ValorPixresidualnaodevolvido": _money(valor_aceito * 0.37),
        "Quantidadedenaodevolvidossaldoinsuficiente": str(saldo),
        "ValorPixnaodevolvidossaldoinsuficiente": _money(valor_aceito * 0.16),
        "Quantidadedenaodevolvidoscontaencerrada": str(closed),
        "Valornaodevolvidoscontaencerrada": _money(valor_aceito * 0.06),
        "Quantidadedenaodevolvidosmotivosdiversos": str(other),
        "ValorPixnaodevolvidosmotivosdiversos": _money(valor_aceito * 0.15),
        "PercentualdeDevolucao": f"{46 + (index % 9) * 0.7:.1f}",
        "QtdePixbloqueadoscautelarmenteeliberados": "0",
        "ValorPixbloqueadoscautelarmenteeliberados": "0",
        "QtdePixbloqueadoscautelarmenteedevolvidos": "0",
        "ValorPixbloqueadoscautelarmenteedevolvidos": "0",
    }


def write_demo(root: Path) -> None:
    """Replace the demo raw zone. Does not touch data/raw from `make ingest`."""

    for ano_mes in months(202201, 202610):
        _write(root, TRANSACOES, ano_mes, _transactions(ano_mes, partial=False))
        _write(root, USUARIOS, ano_mes, _dict_users(ano_mes))
    _write(root, TRANSACOES, 202611, _transactions(202611, partial=True))
    _write(root, USUARIOS, 202611, _dict_users(202611))
    for ano_mes in months(202509, 202610):
        _write(root, MUNICIPIO, ano_mes, _municipalities(ano_mes, partial=False))
        _write(root, CHAVES, ano_mes, _keys(ano_mes))
        _write(root, CNAE, ano_mes, _cnae(ano_mes))
    _write(root, MUNICIPIO, 202611, _municipalities(202611, partial=True))
    _write(root, CHAVES, 202611, _keys(202611))
    for ano_mes in months(202201, 202609):
        _write(root, FRAUDES, ano_mes, [_fraud_measures(ano_mes)])
