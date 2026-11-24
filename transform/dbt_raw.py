"""DuckDB connection plugin that points dbt sources at the raw Parquet zone.

Each cursor sets a file-list variable. Source ``external_location`` entries
call ``read_parquet(getvariable(...))``. An empty partition glob reads a
zero-row sentinel with the writer schema, so ``make model`` still builds the
seeded dimensions when CDC or BCB files are absent.

Variables are connection-local in DuckDB and do not survive ``cursor()``.
``configure_cursor`` sets them on every cursor dbt opens.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from dbt.adapters.duckdb.plugins import BasePlugin
from ingestion.bcb.entities import CHAVES, MUNICIPIO, TRANSACOES, EntitySpec

from transform.sources import (
    S3Raw,
    app_parquet_glob,
    location_from_env,
    parquet_glob,
    s3_statements,
    sql_literal,
)

_LOCK = threading.Lock()
_SENTINELS_READY = False

_BCB: tuple[tuple[str, EntitySpec], ...] = (
    ("estatisticas_transacoes_pix", TRANSACOES),
    ("transacoes_pix_municipio", MUNICIPIO),
    ("chaves_pix", CHAVES),
)

_APP: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "app_pix_keys",
        (
            "op",
            "lsn",
            "lsn_ord",
            "commit_ts",
            "pk",
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
    ),
    (
        "app_pix_transactions",
        (
            "op",
            "lsn",
            "lsn_ord",
            "commit_ts",
            "pk",
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
    ),
    (
        "app_pix_disputes",
        (
            "op",
            "lsn",
            "lsn_ord",
            "commit_ts",
            "pk",
            "id",
            "transaction_id",
            "reason",
            "status",
            "opened_at",
            "resolved_at",
            "created_at",
            "updated_at",
        ),
    ),
)


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _empty_type(arrow_type: object) -> str:
    text = str(arrow_type)
    if text.startswith("int32"):
        return "integer"
    if text.startswith("int64"):
        return "bigint"
    if text.startswith("decimal"):
        return text.replace("decimal128", "decimal")
    if text.startswith("date"):
        return "date"
    if text.startswith("string") or text.startswith("large_string"):
        return "varchar"
    raise TypeError(f"unsupported sentinel type {arrow_type}")


def _bcb_select(spec: EntitySpec) -> str:
    columns = ", ".join(
        f"cast(null as {_empty_type(field.type)}) as {_quote(field.name)}" for field in spec.schema
    )
    return f"select {columns} where false"


def _app_select(columns: tuple[str, ...]) -> str:
    body = ", ".join(f"cast(null as varchar) as {_quote(name)}" for name in columns)
    return f"select {body} where false"


def _sentinel_path(root: Path, name: str, partition: str) -> Path:
    return root / name / partition / "part.parquet"


def _write_sentinels(cursor: Any, root: Path) -> None:
    specs: list[tuple[str, str, str]] = []
    for name, entity in _BCB:
        specs.append((name, "ano_mes=000000", _bcb_select(entity)))
    for name, columns in _APP:
        specs.append((name, "dt=1970-01-01", _app_select(columns)))
    for name, partition, select in specs:
        path = _sentinel_path(root, name, partition)
        path.parent.mkdir(parents=True, exist_ok=True)
        target = sql_literal(path.as_posix())
        cursor.execute(f"copy ({select}) to {target} (format parquet)").fetchall()


def _set_variable(cursor: Any, name: str, glob: str, sentinel: Path) -> None:
    cursor.execute(
        f"""
        set variable pix_raw_{name} = (
            select case
                when count(*) = 0 then [{sql_literal(sentinel.as_posix())}]
                else list(file)
            end
            from glob({sql_literal(glob)})
        )
        """
    ).fetchall()


class Plugin(BasePlugin):
    """dbt-duckdb plugin. The class name is the adapter's import contract."""

    def initialize(self, plugin_config: dict[str, Any]) -> None:
        self._config = plugin_config

    def configure_connection(self, conn: Any) -> None:
        self._configure(conn)

    def configure_cursor(self, cursor: Any) -> None:
        self._configure(cursor)

    def _configure(self, cursor: Any) -> None:
        global _SENTINELS_READY
        location = location_from_env()
        if isinstance(location, S3Raw):
            for statement in s3_statements(location):
                cursor.execute(statement).fetchall()
        root = Path(__file__).resolve().parent / "dbt" / "target" / "empty"
        with _LOCK:
            if not _SENTINELS_READY:
                _write_sentinels(cursor, root)
                _SENTINELS_READY = True
        for name, entity in _BCB:
            _set_variable(
                cursor,
                name,
                parquet_glob(location, entity.name),
                _sentinel_path(root, name, "ano_mes=000000"),
            )
        for name, _columns in _APP:
            table = name.removeprefix("app_")
            _set_variable(
                cursor,
                name,
                app_parquet_glob(location, table),
                _sentinel_path(root, name, "dt=1970-01-01"),
            )
