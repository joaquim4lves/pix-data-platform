"""``python -m transform build`` and ``python -m transform dq``.

Both commands delegate to dbt. ``build`` seeds and runs the models.
``dq`` runs ``dbt test``. The legacy SQL runner remains importable for the
parity test; it is not what ``make model`` calls.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import duckdb

FACTS = (
    "fct_transacoes_mensal",
    "fct_transacoes_municipio",
    "fct_chaves_pix",
    "cur_pix_key",
    "cur_pix_transaction",
    "cur_pix_dispute",
)

_PROJECT = Path(__file__).resolve().parent / "dbt"


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    database = Path(os.environ.get("PIX_DUCKDB_PATH", "data/pix.duckdb"))
    if args.command == "build":
        return _build(database)
    return _dq()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="transform")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="build the local DuckDB warehouse with dbt")
    sub.add_parser("dq", help="run dbt tests against the warehouse")
    return parser


def dbt_command(args: list[str]) -> list[str]:
    return [
        sys.executable,
        "-m",
        "transform.dbt_main",
        *args,
        "--project-dir",
        str(_PROJECT),
        "--profiles-dir",
        str(_PROJECT),
    ]


def run_dbt(args: list[str]) -> int:
    completed = subprocess.run(dbt_command(args))
    return completed.returncode


def _build(database: Path) -> int:
    if run_dbt(["seed"]) != 0:
        return 1
    if run_dbt(["run"]) != 0:
        return 1
    try:
        _print_summary(database)
    except (duckdb.Error, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


def _dq() -> int:
    code = run_dbt(["test"])
    _print_tests()
    return code


def _print_tests() -> None:
    path = _PROJECT / "target" / "run_results.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    for result in payload.get("results", []):
        unique_id = str(result.get("unique_id", ""))
        if not unique_id.startswith("test."):
            continue
        name = unique_id.rsplit(".", 1)[-1]
        failures = result.get("failures")
        violations = 0 if failures is None else int(failures)
        status = "ok" if result.get("status") == "pass" and violations == 0 else "failed"
        print(f"{name} {status} violations={violations}")


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
