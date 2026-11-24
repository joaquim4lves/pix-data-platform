"""Build the local DuckDB file from plain SQL models.

Each file under ``transform/sql`` is one model: the file body is a single
SELECT. Seeds, staging, and intermediate become views. Marts become tables
so the DuckDB file keeps a snapshot after the raw files move. v0.5 dbt can
take the same files; the schema names are the porting seam.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pyarrow as pa
from cdc.tables import APP_TABLES, AppTable
from ingestion.bcb.entities import CHAVES, MUNICIPIO, TRANSACOES, EntitySpec

from transform.sources import (
    LocalRaw,
    RawLocation,
    S3Raw,
    app_parquet_glob,
    parquet_glob,
    s3_statements,
    sql_literal,
)

SQL_DIR = Path(__file__).resolve().parent / "sql"

RAW_TABLES: tuple[tuple[str, EntitySpec], ...] = (
    ("estatisticas_transacoes_pix", TRANSACOES),
    ("transacoes_pix_municipio", MUNICIPIO),
    ("chaves_pix", CHAVES),
)

LAYERS: tuple[tuple[str, str], ...] = (
    ("seeds", "VIEW"),
    ("staging", "VIEW"),
    ("intermediate", "VIEW"),
    ("marts", "TABLE"),
)

SCHEMAS = ("raw", "seeds", "staging", "intermediate", "marts")


def build_warehouse(database: Path, location: RawLocation) -> None:
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(database))
    try:
        if isinstance(location, S3Raw):
            for statement in s3_statements(location):
                con.execute(statement)
        for schema in reversed(SCHEMAS):
            con.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        for schema in SCHEMAS:
            con.execute(f"CREATE SCHEMA {schema}")
        _create_raw_views(con, location)
        _create_app_views(con, location)
        for layer, kind in LAYERS:
            _apply_layer(con, layer, kind)
    finally:
        con.close()


def _create_raw_views(con: duckdb.DuckDBPyConnection, location: RawLocation) -> None:
    for name, spec in RAW_TABLES:
        select = _raw_select(con, location, spec)
        _execute(con, f"CREATE OR REPLACE VIEW raw.{name} AS\n{select}", label=f"raw.{name}")


def _raw_select(con: duckdb.DuckDBPyConnection, location: RawLocation, spec: EntitySpec) -> str:
    glob = parquet_glob(location, spec.name)
    scan = f"SELECT * FROM read_parquet({sql_literal(glob)}, hive_partitioning=true)"
    if isinstance(location, LocalRaw):
        folder = location.root / "bcb" / spec.name
        if not any(folder.glob("ano_mes=*/part.parquet")):
            return _empty_select(spec.schema)
        return scan
    try:
        con.execute(scan + " LIMIT 0")
    except duckdb.Error as exc:
        if "No files found" in str(exc):
            return _empty_select(spec.schema)
        raise
    return scan


def _create_app_views(con: duckdb.DuckDBPyConnection, location: RawLocation) -> None:
    for spec in APP_TABLES.values():
        select = _app_select(con, location, spec)
        _execute(
            con,
            f"CREATE OR REPLACE VIEW raw.app_{spec.name} AS\n{select}",
            label=f"raw.app_{spec.name}",
        )


def _app_select(con: duckdb.DuckDBPyConnection, location: RawLocation, spec: AppTable) -> str:
    glob = app_parquet_glob(location, spec.name)
    scan = f"SELECT * FROM read_parquet({sql_literal(glob)}, hive_partitioning=true)"
    if isinstance(location, LocalRaw):
        folder = location.root / "app" / spec.name
        if not any(folder.glob("dt=*/*.parquet")):
            return _empty_app_select(spec)
        return scan
    try:
        con.execute(scan + " LIMIT 0")
    except duckdb.Error as exc:
        if "No files found" in str(exc):
            return _empty_app_select(spec)
        raise
    return scan


def _empty_app_select(spec: AppTable) -> str:
    columns = ", ".join(f"CAST(NULL AS VARCHAR) AS {_quote(name)}" for name in spec.parquet_columns)
    return f"SELECT {columns} WHERE FALSE"


def _empty_select(schema: pa.Schema) -> str:
    columns = ", ".join(
        f"CAST(NULL AS {_sql_type(field.type)}) AS {_quote(field.name)}" for field in schema
    )
    return f"SELECT {columns} WHERE FALSE"


def _sql_type(typ: pa.DataType) -> str:
    if pa.types.is_int32(typ):
        return "INTEGER"
    if pa.types.is_int64(typ):
        return "BIGINT"
    if pa.types.is_string(typ) or pa.types.is_large_string(typ):
        return "VARCHAR"
    if pa.types.is_decimal(typ):
        return f"DECIMAL({typ.precision}, {typ.scale})"
    if pa.types.is_date(typ):
        return "DATE"
    raise TypeError(f"unsupported raw column type {typ}")


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _apply_layer(con: duckdb.DuckDBPyConnection, layer: str, kind: str) -> None:
    folder = SQL_DIR / layer
    paths = sorted(folder.glob("*.sql"))
    if not paths:
        raise FileNotFoundError(f"no SQL models in {folder}")
    for path in paths:
        body = path.read_text(encoding="utf-8").strip()
        if body.endswith(";"):
            body = body[:-1].rstrip()
        relation = f"{layer}.{path.stem}"
        _execute(con, f"CREATE OR REPLACE {kind} {relation} AS\n{body}", label=str(path))


def _execute(con: duckdb.DuckDBPyConnection, sql: str, *, label: str) -> None:
    try:
        con.execute(sql)
    except duckdb.Error as exc:
        raise RuntimeError(f"{label} failed: {exc}") from exc
