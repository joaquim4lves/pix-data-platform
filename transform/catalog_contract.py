"""Glue column contract derived from the Parquet writers.

Terraform reads ``infra/terraform/modules/catalog/columns.json``. The test
compares that file to ``catalog_document()``, so a schema change in the
writers fails CI until the JSON is regenerated.
"""

from __future__ import annotations

import pyarrow as pa
from cdc.tables import PIX_DISPUTES, PIX_KEYS, PIX_TRANSACTIONS, AppTable
from ingestion.bcb.entities import CHAVES, MUNICIPIO, TRANSACOES, EntitySpec


def glue_type(arrow_type: pa.DataType) -> str:
    if pa.types.is_int32(arrow_type):
        return "int"
    if pa.types.is_int64(arrow_type):
        return "bigint"
    if pa.types.is_string(arrow_type) or pa.types.is_large_string(arrow_type):
        return "string"
    if pa.types.is_date32(arrow_type):
        return "date"
    if pa.types.is_decimal(arrow_type):
        return f"decimal({arrow_type.precision},{arrow_type.scale})"
    raise TypeError(f"no Glue type for {arrow_type!s}")


def _bcb(table: str, spec: EntitySpec, description: str) -> dict[str, object]:
    return {
        "table": table,
        "folder": spec.name,
        "description": description,
        "columns": [{"name": field.name, "type": glue_type(field.type)} for field in spec.schema],
    }


def _app(spec: AppTable, description: str) -> dict[str, object]:
    return {
        "table": f"app_{spec.name}",
        "folder": spec.name,
        "description": description,
        "columns": [{"name": name, "type": "string"} for name in spec.parquet_columns],
    }


def catalog_document() -> dict[str, list[dict[str, object]]]:
    return {
        "bcb": [
            _bcb(
                "estatisticas_transacoes_pix",
                TRANSACOES,
                "Olinda EstatisticasTransacoesPix. One Parquet file per ano_mes partition.",
            ),
            _bcb(
                "transacoes_pix_municipio",
                MUNICIPIO,
                "Olinda TransacoesPixPorMunicipio, including the published N/D municipality.",
            ),
            _bcb(
                "chaves_pix",
                CHAVES,
                "Olinda ChavesPix stock snapshot. The Hive partition is ano_mes, not Data.",
            ),
        ],
        "app": [
            _app(PIX_KEYS, "CDC log of pix_keys. Every column is the text pgoutput emitted."),
            _app(PIX_TRANSACTIONS, "CDC log of pix_transactions."),
            _app(PIX_DISPUTES, "CDC log of pix_disputes."),
        ],
    }
