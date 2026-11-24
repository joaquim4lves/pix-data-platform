"""Command line for ingest, backfill, and bucket bootstrap."""

from __future__ import annotations

import argparse
import os

from ingestion.bcb.calendar import parse_ano_mes
from ingestion.bcb.logging import configure_logging
from ingestion.bcb.pipeline import RunResult, run, select_entities
from ingestion.bcb.settings import Settings
from ingestion.bcb.store import ObjectStore


def main(argv: list[str] | None = None) -> int:
    configure_logging(os.environ.get("LOG_LEVEL", "INFO"))
    args = _parser().parse_args(argv)
    settings = Settings.from_env()
    if args.command == "ensure-bucket":
        ObjectStore.from_settings(settings).ensure_bucket()
        print(f"bucket ready: {settings.bucket}")
        return 0
    names = _entity_names(args.entities)
    if args.command == "ingest":
        result = run(
            settings,
            mode="ingest",
            lookback_months=args.lookback_months,
            entities=names,
        )
    else:
        result = run(
            settings,
            mode="backfill",
            start=args.start,
            end=args.end,
            entities=names,
        )
    _print_summary(result)
    return 0 if result.ok else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ingestion.bcb")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="reprocess the recent window")
    ingest.add_argument("--lookback-months", type=int, default=None)
    ingest.add_argument("--entities", default=None, help="comma-separated entity names")

    backfill = sub.add_parser("backfill", help="load an inclusive YYYYMM range")
    backfill.add_argument("--start", required=True, type=_ano_mes_arg)
    backfill.add_argument("--end", required=True, type=_ano_mes_arg)
    backfill.add_argument("--entities", default=None, help="comma-separated entity names")

    sub.add_parser("ensure-bucket", help="create the raw bucket when it is missing")
    return parser


def _ano_mes_arg(value: str) -> int:
    try:
        return parse_ano_mes(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _entity_names(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    names = [part.strip() for part in raw.split(",") if part.strip()]
    select_entities(names)
    return names


def _print_summary(result: RunResult) -> None:
    for item in result.entities:
        months = " ".join(f"{month}={count}" for month, count in sorted(item.rows_by_month.items()))
        status = "ok" if item.ok else "failed"
        line = (
            f"{item.entity} {status} rows={item.rows_written} "
            f"watermark={item.watermark} {months}".rstrip()
        )
        if item.error:
            line = f"{line} error={item.error}"
        if item.quarantined_keys:
            line = f"{line} quarantine={','.join(item.quarantined_keys)}"
        print(line)
