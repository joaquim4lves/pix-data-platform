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

ENTITY_ORDER: tuple[EntitySpec, ...] = (TRANSACOES, MUNICIPIO, CHAVES)
ENTITIES: dict[str, EntitySpec] = {spec.name: spec for spec in ENTITY_ORDER}
