"""Operational tables the CDC sink and the DuckDB models share.

The Parquet log stores one string column per business field plus the
envelope coordinates. Staging casts the strings. Keeping the list here
stops the writer and the empty raw view from drifting apart.
"""

from __future__ import annotations

from dataclasses import dataclass

META_COLUMNS = ("op", "lsn", "lsn_ord", "commit_ts", "pk")


@dataclass(frozen=True)
class AppTable:
    name: str
    pk: tuple[str, ...]
    columns: tuple[str, ...]

    @property
    def parquet_columns(self) -> tuple[str, ...]:
        return META_COLUMNS + self.columns


PIX_KEYS = AppTable(
    name="pix_keys",
    pk=("id",),
    columns=(
        "id",
        "key_type",
        "key_value",
        "person_type",
        "ispb",
        "municipio_ibge",
        "status",
        "created_at",
        "updated_at",
    ),
)

PIX_TRANSACTIONS = AppTable(
    name="pix_transactions",
    pk=("id",),
    columns=(
        "id",
        "end_to_end_id",
        "amount",
        "payer_ispb",
        "receiver_ispb",
        "municipio_ibge",
        "forma_iniciacao",
        "direction",
        "status",
        "occurred_at",
        "created_at",
        "updated_at",
    ),
)

PIX_DISPUTES = AppTable(
    name="pix_disputes",
    pk=("id",),
    columns=(
        "id",
        "transaction_id",
        "reason",
        "status",
        "opened_at",
        "resolved_at",
        "created_at",
        "updated_at",
    ),
)

APP_TABLES: dict[str, AppTable] = {
    table.name: table for table in (PIX_KEYS, PIX_TRANSACTIONS, PIX_DISPUTES)
}
