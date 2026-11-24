"""``python -m payments migrate|serve|load``."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from payments.seed import load_operational
from payments.settings import database_url

INI = Path(__file__).resolve().parent / "alembic.ini"
MIGRATIONS = Path(__file__).resolve().parent / "migrations"


def migrate(url: str | None = None) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(INI))
    cfg.set_main_option("script_location", str(MIGRATIONS))
    # Config interpolates %. A password that contains % must be escaped.
    cfg.set_main_option("sqlalchemy.url", (url or database_url()).replace("%", "%%"))
    command.upgrade(cfg, "head")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "migrate":
            migrate()
            print("migrated")
            return 0
        if args.command == "serve":
            migrate()
            import uvicorn

            uvicorn.run(
                "payments.api:app",
                host=os.environ.get("API_HOST", "0.0.0.0"),
                port=int(os.environ.get("API_PORT", "8000")),
            )
            return 0
        report = load_operational(
            database_url(),
            seed=args.seed,
            keys=args.keys,
            transactions=args.transactions,
            disputes=args.disputes,
            reset=args.reset,
        )
    except Exception as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"loaded inserted={report.inserted} updated={report.updated} deleted={report.deleted}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="payments")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate", help="apply Alembic migrations")
    sub.add_parser("serve", help="migrate, then serve the API")
    load = sub.add_parser("load", help="insert, update, and delete sample operational rows")
    load.add_argument("--seed", type=int, default=7)
    load.add_argument("--keys", type=int, default=12)
    load.add_argument("--transactions", type=int, default=20)
    load.add_argument("--disputes", type=int, default=6)
    load.add_argument(
        "--reset",
        action="store_true",
        help="delete existing rows first, one commit each",
    )
    return parser
