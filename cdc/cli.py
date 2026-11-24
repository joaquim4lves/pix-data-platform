"""``python -m cdc consume|apply|e2e``."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from cdc.apply import apply_queue
from cdc.consumer import consume
from cdc.pipeline import assert_current_state, require_localstack, run_pipeline, sync_app_parquet
from cdc.settings import CdcSettings


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    settings = CdcSettings.from_env()
    try:
        if args.command == "consume":
            from payments.cli import migrate

            migrate(settings.database_url)
            result = consume(settings, once=args.once)
            target = result.advanced_to or "unchanged"
            print(f"cdc published={result.published} advanced_to={target}")
            return 0
        if args.command == "apply":
            result = apply_queue(settings)
            print(f"apply deleted={result.deleted} failed={result.failed}")
            return 1 if result.failed else 0
        require_localstack(settings)
        pipeline = run_pipeline(settings, reset=True)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "raw"
            files = sync_app_parquet(settings, root)
            assert_current_state(settings, pipeline.load, root)
        print(
            "e2e "
            f"published={pipeline.consume.published} "
            f"parquet_files={files} "
            f"advanced_to={pipeline.consume.advanced_to}"
        )
        return 0
    except Exception as exc:
        print(exc, file=sys.stderr)
        return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cdc")
    sub = parser.add_subparsers(dest="command", required=True)
    consume_parser = sub.add_parser("consume", help="publish logical changes to SQS")
    consume_parser.add_argument(
        "--once",
        action="store_true",
        help="drain the slot and exit instead of waiting for more commits",
    )
    sub.add_parser("apply", help="write queued change events to S3 as Parquet")
    sub.add_parser("e2e", help="recreate the slot, load, drain, and check current state")
    return parser
