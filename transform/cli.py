"""``python -m transform build`` and ``python -m transform dq``."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import duckdb

from transform.build import build_warehouse
from transform.checks import run_checks
from transform.sources import location_from_env

FACTS = (
    "fct_transacoes_mensal",
    "fct_transacoes_municipio",
    "fct_chaves_pix",
    "cur_pix_key",
    "cur_pix_transaction",
    "cur_pix_dispute",
)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    database = Path(os.environ.get("PIX_DUCKDB_PATH", "data/pix.duckdb"))
    if args.command == "build":
        return _build(database)
    return _dq(database)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="transform")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="build the local DuckDB warehouse from raw Parquet")
    sub.add_parser("dq", help="run data-quality checks against the warehouse")
    return parser


def _build(database: Path) -> int:
    try:
        location = location_from_env()
        build_warehouse(database, location)
    except (RuntimeError, duckdb.Error, ValueError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    _print_summary(database)
    return 0


def _dq(database: Path) -> int:
    try:
        results = run_checks(database)
    except (RuntimeError, duckdb.Error, FileNotFoundError) as exc:
        print(exc, file=sys.stderr)
        return 1
    failed = False
    for item in results:
        status = "ok" if item.ok else "failed"
        print(f"{item.name} {status} violations={item.violations}")
        failed = failed or not item.ok
    return 1 if failed else 0


def _print_summary(database: Path) -> None:
    con = duckdb.connect(str(database), read_only=True)
    try:
        print(f"warehouse {database}")
        for name in FACTS:
            count = con.execute(f"select count(*) from marts.{name}").fetchone()
            rows = 0 if count is None else count[0]
            print(f"marts.{name} rows={rows}")
    finally:
        con.close()
