"""Schema contracts for the three core PIX resources.

Field names and types follow the Olinda ``$metadata`` and the JSON observed
on 2026-11-24. Codes such as ``NATUREZA`` and ``FORMAINICIACAO`` are stored
as the API sent them. This module does not translate them into labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pyarrow as pa
from pydantic import BaseModel, ConfigDict

DECIMAL = pa.decimal128(38, 8)

# Raw codes present in the full EstatisticasTransacoesPix month of 202610.
# Used only to slice a saturated page. Not a display dictionary.
NATUREZA_CODES = ("B2B", "B2G", "B2P", "G2B", "G2G", "G2P", "P2B", "P2G", "P2P")

# Raw TipoChave values present in the ChavesPix snapshot of 2026-10-31.
TIPO_CHAVE_VALUES = ("Aleatória", "CNPJ", "CPF", "Celular", "e-mail")


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EstatisticasTransacoesPix(_Contract):
    AnoMes: int
    PAG_PFPJ: str
    REC_PFPJ: str
    PAG_REGIAO: str
    REC_REGIAO: str
    PAG_IDADE: str
    REC_IDADE: str
    FORMAINICIACAO: str
    NATUREZA: str
    FINALIDADE: str
    VALOR: Decimal
    QUANTIDADE: Decimal


class TransacoesPixPorMunicipio(_Contract):
    AnoMes: int
    # One published row per month is the "not informed" bucket: IBGE and region code are null.
    Municipio_Ibge: int | None
    Municipio: str
    Estado_Ibge: int | None
    Estado: str
    Sigla_Regiao: str | None
    Regiao: str
    VL_PagadorPF: Decimal
    QT_PagadorPF: Decimal
    VL_PagadorPJ: Decimal
    QT_PagadorPJ: Decimal
    VL_RecebedorPF: Decimal
    QT_RecebedorPF: Decimal
    VL_RecebedorPJ: Decimal
    QT_RecebedorPJ: Decimal
    QT_PES_PagadorPF: Decimal
    QT_PES_PagadorPJ: Decimal
    QT_PES_RecebedorPF: Decimal
    QT_PES_RecebedorPJ: Decimal


class ChavesPix(_Contract):
    Data: date
    ISPB: str
    Nome: str
    NaturezaUsuario: str
    TipoChave: str
    qtdChaves: int
    Segmento: str


def _string(name: str) -> pa.Field:
    return pa.field(name, pa.string(), nullable=False)


def _int(name: str, typ: pa.DataType) -> pa.Field:
    return pa.field(name, typ, nullable=False)


def _decimal(name: str) -> pa.Field:
    return pa.field(name, DECIMAL, nullable=False)


TRANSACOES_SCHEMA = pa.schema(
    [
        _int("AnoMes", pa.int32()),
        _string("PAG_PFPJ"),
        _string("REC_PFPJ"),
        _string("PAG_REGIAO"),
        _string("REC_REGIAO"),
        _string("PAG_IDADE"),
        _string("REC_IDADE"),
        _string("FORMAINICIACAO"),
        _string("NATUREZA"),
        _string("FINALIDADE"),
        _decimal("VALOR"),
        _decimal("QUANTIDADE"),
    ]
)

MUNICIPIO_SCHEMA = pa.schema(
    [
        _int("AnoMes", pa.int32()),
        pa.field("Municipio_Ibge", pa.int32(), nullable=True),
        _string("Municipio"),
        pa.field("Estado_Ibge", pa.int32(), nullable=True),
        _string("Estado"),
        pa.field("Sigla_Regiao", pa.string(), nullable=True),
        _string("Regiao"),
        _decimal("VL_PagadorPF"),
        _decimal("QT_PagadorPF"),
        _decimal("VL_PagadorPJ"),
        _decimal("QT_PagadorPJ"),
        _decimal("VL_RecebedorPF"),
        _decimal("QT_RecebedorPF"),
        _decimal("VL_RecebedorPJ"),
        _decimal("QT_RecebedorPJ"),
        _decimal("QT_PES_PagadorPF"),
        _decimal("QT_PES_PagadorPJ"),
        _decimal("QT_PES_RecebedorPF"),
        _decimal("QT_PES_RecebedorPJ"),
    ]
)

CHAVES_SCHEMA = pa.schema(
    [
        pa.field("Data", pa.date32(), nullable=False),
        _string("ISPB"),
        _string("Nome"),
        _string("NaturezaUsuario"),
        _string("TipoChave"),
        _int("qtdChaves", pa.int64()),
        _string("Segmento"),
    ]
)


@dataclass
class EntitySpec:
    name: str
    resource: str
    param_name: str
    period: str
    model: type[_Contract]
    schema: pa.Schema
    sort_columns: tuple[str, ...]
    split_field: str | None = None
    split_values: tuple[str, ...] = ()


TRANSACOES = EntitySpec(
    name="EstatisticasTransacoesPix",
    resource="EstatisticasTransacoesPix",
    param_name="Database",
    period="ano_mes",
    model=EstatisticasTransacoesPix,
    schema=TRANSACOES_SCHEMA,
    sort_columns=(
        "AnoMes",
        "PAG_PFPJ",
        "REC_PFPJ",
        "PAG_REGIAO",
        "REC_REGIAO",
        "PAG_IDADE",
        "REC_IDADE",
        "FORMAINICIACAO",
        "NATUREZA",
        "FINALIDADE",
    ),
    split_field="NATUREZA",
    split_values=NATUREZA_CODES,
)

MUNICIPIO = EntitySpec(
    name="TransacoesPixPorMunicipio",
    resource="TransacoesPixPorMunicipio",
    param_name="DataBase",
    period="ano_mes",
    model=TransacoesPixPorMunicipio,
    schema=MUNICIPIO_SCHEMA,
    sort_columns=("AnoMes", "Municipio_Ibge"),
)

CHAVES = EntitySpec(
    name="ChavesPix",
    resource="ChavesPix",
    param_name="Data",
    period="date",
    model=ChavesPix,
    schema=CHAVES_SCHEMA,
    sort_columns=("Data", "ISPB", "NaturezaUsuario", "TipoChave", "Segmento", "Nome"),
    split_field="TipoChave",
    split_values=TIPO_CHAVE_VALUES,
)


class EstatisticasFraudesPix(_Contract):
    """National MED month. Every measure is Edm.Decimal on Olinda except AnoMes."""

    AnoMes: int
    QtdePixcontestados: Decimal
    Qtdecontestacoesaceitas: Decimal
    Qtdecontestacoesrejeitadas: Decimal
    Qtdecontestacoesaceitasacada100mil: Decimal
    QtdeUsuarioscommarcacoesdefraude: Decimal
    QtdeChavesPixcommarcacoesdefraude: Decimal
    ValorPixcontestadosaceitos: Decimal
    QuantidadedevolvidaintegralmentepormeiodoMED: Decimal
    ValorPixdevolvidosintegralmente: Decimal
    QuantidadedevolvidaparcialmentepormeiodoMED: Decimal
    ValorPixdevolvidosparcialmente: Decimal
    ValorPixresidualnaodevolvido: Decimal
    Quantidadedenaodevolvidossaldoinsuficiente: Decimal
    ValorPixnaodevolvidossaldoinsuficiente: Decimal
    Quantidadedenaodevolvidoscontaencerrada: Decimal
    Valornaodevolvidoscontaencerrada: Decimal
    Quantidadedenaodevolvidosmotivosdiversos: Decimal
    ValorPixnaodevolvidosmotivosdiversos: Decimal
    PercentualdeDevolucao: Decimal
    QtdePixbloqueadoscautelarmenteeliberados: Decimal
    ValorPixbloqueadoscautelarmenteeliberados: Decimal
    QtdePixbloqueadoscautelarmenteedevolvidos: Decimal
    ValorPixbloqueadoscautelarmenteedevolvidos: Decimal


class CnaePorteRecebedor(_Contract):
    AnoMes: int
    tipopessoa: str
    formainic: str
    finalidade: str
    porte: str
    mei: str
    cnssecao: str
    mesmatit: str
    naturezarel: str
    qtpagador: Decimal
    qtrecebedor: Decimal
    qtlanliq: Decimal
    vllanliq: Decimal
    vlcompra: Decimal
    vldinespec: Decimal


class PixUsuariosCadastradosDICT(_Contract):
    DataGraficosPix: date
    qtdUsuariosPessoaFisica: int
    qtdUsuariosPessoaJuridica: int
    qtdUsuariosCadastradosDICTTotal: int


def _fraud_schema() -> pa.Schema:
    fields = [_int("AnoMes", pa.int32())]
    for name in (
        "QtdePixcontestados",
        "Qtdecontestacoesaceitas",
        "Qtdecontestacoesrejeitadas",
        "Qtdecontestacoesaceitasacada100mil",
        "QtdeUsuarioscommarcacoesdefraude",
        "QtdeChavesPixcommarcacoesdefraude",
        "ValorPixcontestadosaceitos",
        "QuantidadedevolvidaintegralmentepormeiodoMED",
        "ValorPixdevolvidosintegralmente",
        "QuantidadedevolvidaparcialmentepormeiodoMED",
        "ValorPixdevolvidosparcialmente",
        "ValorPixresidualnaodevolvido",
        "Quantidadedenaodevolvidossaldoinsuficiente",
        "ValorPixnaodevolvidossaldoinsuficiente",
        "Quantidadedenaodevolvidoscontaencerrada",
        "Valornaodevolvidoscontaencerrada",
        "Quantidadedenaodevolvidosmotivosdiversos",
        "ValorPixnaodevolvidosmotivosdiversos",
        "PercentualdeDevolucao",
        "QtdePixbloqueadoscautelarmenteeliberados",
        "ValorPixbloqueadoscautelarmenteeliberados",
        "QtdePixbloqueadoscautelarmenteedevolvidos",
        "ValorPixbloqueadoscautelarmenteedevolvidos",
    ):
        fields.append(_decimal(name))
    return pa.schema(fields)


FRAUDES_SCHEMA = _fraud_schema()

CNAE_SCHEMA = pa.schema(
    [
        _int("AnoMes", pa.int32()),
        _string("tipopessoa"),
        _string("formainic"),
        _string("finalidade"),
        _string("porte"),
        _string("mei"),
        _string("cnssecao"),
        _string("mesmatit"),
        _string("naturezarel"),
        _decimal("qtpagador"),
        _decimal("qtrecebedor"),
        _decimal("qtlanliq"),
        _decimal("vllanliq"),
        _decimal("vlcompra"),
        _decimal("vldinespec"),
    ]
)

USUARIOS_SCHEMA = pa.schema(
    [
        pa.field("DataGraficosPix", pa.date32(), nullable=False),
        _int("qtdUsuariosPessoaFisica", pa.int64()),
        _int("qtdUsuariosPessoaJuridica", pa.int64()),
        _int("qtdUsuariosCadastradosDICTTotal", pa.int64()),
    ]
)

FRAUDES = EntitySpec(
    name="EstatisticasFraudesPix",
    resource="EstatisticasFraudesPix",
    param_name="Database",
    period="ano_mes",
    model=EstatisticasFraudesPix,
    schema=FRAUDES_SCHEMA,
    sort_columns=("AnoMes",),
)

CNAE = EntitySpec(
    name="CnaePorteRecebedor",
    resource="CnaePorteRecebedor",
    param_name="Database",
    period="ano_mes",
    model=CnaePorteRecebedor,
    schema=CNAE_SCHEMA,
    sort_columns=("AnoMes", "tipopessoa", "cnssecao", "porte", "mei", "naturezarel"),
)

USUARIOS = EntitySpec(
    name="PixUsuariosCadastradosDICT",
    resource="PixUsuariosCadastradosDICT",
    param_name="",
    period="date",
    model=PixUsuariosCadastradosDICT,
    schema=USUARIOS_SCHEMA,
    sort_columns=("DataGraficosPix",),
)

ENTITY_ORDER: tuple[EntitySpec, ...] = (TRANSACOES, MUNICIPIO, CHAVES)
ENTITIES: dict[str, EntitySpec] = {spec.name: spec for spec in ENTITY_ORDER}

# Seeded for the v1.0 dashboards. Not part of live ingest: PixUsuariosCadastradosDICT
# is an entity set (no function import), and these three are not in the v0.1 watermark.
DASHBOARD_SPECS: tuple[EntitySpec, ...] = (FRAUDES, CNAE, USUARIOS)
