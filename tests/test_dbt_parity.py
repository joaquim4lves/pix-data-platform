"""dbt output matches the legacy SQL runner on the same fixture Parquet."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import duckdb
from tests.pix_warehouse import write_sample_raw
from tests.test_cdc_merge import _event, _image, _write
from transform.build import build_warehouse
from transform.cli import dbt_command
from transform.dbt_raw import Plugin
from transform.sources import LocalRaw

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ("seeds", "staging", "intermediate", "marts")


def _norm(value: object) -> object:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return value
    return value


def _run_dbt(raw: Path, database: Path, *args: str) -> None:
    env = os.environ.copy()
    env["PIX_RAW_SOURCE"] = "local"
    env["PIX_RAW_ROOT"] = str(raw)
    env["PIX_DUCKDB_PATH"] = str(database)
    completed = subprocess.run(
        dbt_command(list(args)),
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stdout + "\n" + completed.stderr)


def _columns(con: duckdb.DuckDBPyConnection, schema: str, table: str) -> list[str]:
    rows = con.execute(
        """
        select column_name
        from information_schema.columns
        where table_schema = ? and table_name = ?
        order by ordinal_position
        """,
        [schema, table],
    ).fetchall()
    return [row[0] for row in rows]


def _tables(con: duckdb.DuckDBPyConnection) -> list[tuple[str, str]]:
    rows = con.execute(
        """
        select table_schema, table_name
        from information_schema.tables
        where table_schema in ('seeds', 'staging', 'intermediate', 'marts')
        order by 1, 2
        """
    ).fetchall()
    return [(row[0], row[1]) for row in rows]


def _fetch(
    con: duckdb.DuckDBPyConnection, schema: str, table: str, columns: list[str]
) -> list[tuple[object, ...]]:
    quoted = ", ".join(f'"{name}"' for name in columns)
    order = ", ".join(f'"{name}" nulls last' for name in columns)
    rows = con.execute(f"select {quoted} from {schema}.{table} order by {order}").fetchall()
    return [tuple(_norm(value) for value in row) for row in rows]


def _compare(legacy: Path, built: Path, raw: Path) -> None:
    os.environ["PIX_RAW_SOURCE"] = "local"
    os.environ["PIX_RAW_ROOT"] = str(raw)
    left = duckdb.connect(str(legacy), read_only=True)
    right = duckdb.connect(str(built))
    Plugin(name="raw_zone", plugin_config={}).configure_connection(right)
    try:
        assert _tables(left) == _tables(right)
        for schema, table in _tables(left):
            legacy_columns = _columns(left, schema, table)
            dbt_columns = _columns(right, schema, table)
            extra = [name for name in dbt_columns if name not in legacy_columns]
            missing = [name for name in legacy_columns if name not in dbt_columns]
            if table.startswith("cur_"):
                assert extra == ["lsn_ord"], (table, extra)
            else:
                assert extra == [], (table, extra)
            assert missing == [], (table, missing)
            assert _fetch(left, schema, table, legacy_columns) == _fetch(
                right, schema, table, legacy_columns
            ), table
    finally:
        left.close()
        right.close()


def _rows(database: Path, sql: str) -> list[tuple[object, ...]]:
    con = duckdb.connect(str(database), read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def _with_cdc(raw: Path) -> None:
    key_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    base = {
        "key_type": "CPF",
        "key_value": "10000000001",
        "person_type": "PF",
        "ispb": "5938780",
        "municipio_ibge": "3550308",
        "created_at": "2026-11-24T12:00:00.000000Z",
        "updated_at": "2026-11-24T12:00:00.000000Z",
    }
    active = _image("pix_keys", id=key_id, status="active", **base)
    _write(raw, "part-early.parquet", [_event("pix_keys", "insert", "0/10", key_id, after=active)])


def test_dbt_matches_legacy_sql_on_the_fixture(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    write_sample_raw(raw)
    _with_cdc(raw)
    legacy = tmp_path / "legacy.duckdb"
    built = tmp_path / "dbt.duckdb"
    build_warehouse(legacy, LocalRaw(raw))
    _run_dbt(raw, built, "build")
    _compare(legacy, built, raw)


def test_dbt_matches_legacy_sql_when_the_raw_zone_is_empty(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    legacy = tmp_path / "legacy.duckdb"
    built = tmp_path / "dbt.duckdb"
    build_warehouse(legacy, LocalRaw(raw))
    _run_dbt(raw, built, "build")
    _compare(legacy, built, raw)


def test_incremental_cdc_ignores_a_late_older_lsn(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    write_sample_raw(raw)
    key_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    base = {
        "key_type": "CPF",
        "key_value": "10000000001",
        "person_type": "PF",
        "ispb": "5938780",
        "municipio_ibge": "3550308",
        "created_at": "2026-11-24T12:00:00.000000Z",
        "updated_at": "2026-11-24T12:00:00.000000Z",
    }
    active = _image("pix_keys", id=key_id, status="active", **base)
    stale = _image("pix_keys", id=key_id, status="stale", **base)
    final = _image("pix_keys", id=key_id, status="final", **base)
    _write(raw, "part-early.parquet", [_event("pix_keys", "insert", "0/10", key_id, after=active)])
    database = tmp_path / "dbt.duckdb"
    _run_dbt(raw, database, "build")

    _write(
        raw,
        "part-late-old.parquet",
        [_event("pix_keys", "update", "0/05", key_id, before=active, after=stale)],
    )
    _run_dbt(raw, database, "run", "--select", "cur_pix_key")
    assert _rows(database, "select status from marts.cur_pix_key") == [("active",)]

    _write(
        raw,
        "part-late-new.parquet",
        [_event("pix_keys", "update", "0/20", key_id, before=active, after=final)],
    )
    _run_dbt(raw, database, "run", "--select", "cur_pix_key")
    assert _rows(database, "select status, lsn from marts.cur_pix_key") == [("final", "0/20")]

    _write(raw, "part-delete.parquet", [_event("pix_keys", "delete", "0/30", key_id, before=final)])
    _run_dbt(raw, database, "run", "--select", "cur_pix_key")
    assert _rows(database, "select count(*) from marts.cur_pix_key") == [(0,)]


def test_athena_target_parses_without_aws() -> None:
    completed = subprocess.run(
        dbt_command(["parse", "--target", "athena"]),
        cwd=ROOT,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr
    manifest = json.loads((ROOT / "transform" / "dbt" / "target" / "manifest.json").read_text())
    assert manifest["metadata"]["project_name"] == "pix_data_platform"


def test_dbt_invocation_uses_this_interpreter() -> None:
    assert dbt_command(["--version"])[0] == sys.executable
