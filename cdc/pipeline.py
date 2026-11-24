"""Slot, load, queue, and current-state check used by ``make e2e``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import httpx
import psycopg
from botocore.exceptions import ClientError
from payments.cli import migrate
from payments.seed import LoadResult, load_operational
from payments.settings import libpq_url
from transform.build import build_warehouse
from transform.checks import run_checks
from transform.sources import LocalRaw

from cdc.apply import ApplyResult, apply_queue
from cdc.aws import client, error_code
from cdc.consumer import (
    ConsumeResult,
    consume,
    ensure_publication,
    quote_ident,
    recreate_slot,
    require_logical,
)
from cdc.settings import CdcSettings
from cdc.sink import MISSING
from cdc.tables import APP_TABLES

_MART = {
    "pix_keys": "cur_pix_key",
    "pix_transactions": "cur_pix_transaction",
    "pix_disputes": "cur_pix_dispute",
}


@dataclass(frozen=True)
class PipelineResult:
    load: LoadResult
    consume: ConsumeResult
    apply: ApplyResult


def require_localstack(settings: CdcSettings) -> None:
    if not settings.endpoint_url:
        raise RuntimeError("e2e needs AWS_ENDPOINT_URL pointing at LocalStack")
    url = settings.endpoint_url.rstrip("/") + "/_localstack/health"
    try:
        response = httpx.get(url, timeout=2.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"LocalStack is not available at {settings.endpoint_url}. Run make up first."
        ) from exc


def run_pipeline(
    settings: CdcSettings,
    *,
    reset: bool = True,
    seed: int = 7,
    keys: int = 12,
    transactions: int = 20,
    disputes: int = 6,
    apply_wait: int = 1,
) -> PipelineResult:
    migrate(settings.database_url)
    with psycopg.connect(libpq_url(settings.database_url), autocommit=True) as conn:
        require_logical(conn)
        ensure_publication(conn, settings.publication, tuple(APP_TABLES))
        if reset:
            recreate_slot(conn, settings.slot)
        else:
            from cdc.consumer import ensure_slot

            ensure_slot(conn, settings.slot)
    report = load_operational(
        settings.database_url,
        seed=seed,
        keys=keys,
        transactions=transactions,
        disputes=disputes,
        reset=reset,
    )
    consumed = consume(settings, once=True)
    applied = apply_queue(settings, wait_seconds=apply_wait)
    if reset and consumed.published != report.operation_count():
        raise RuntimeError(
            f"published {consumed.published} events but the load recorded "
            f"{report.operation_count()} commits"
        )
    if applied.failed:
        raise RuntimeError(f"SQS apply left {applied.failed} failed messages")
    if reset and applied.deleted != consumed.published:
        raise RuntimeError(
            f"deleted {applied.deleted} queue messages, published {consumed.published}"
        )
    return PipelineResult(report, consumed, applied)


def sync_app_parquet(settings: CdcSettings, root: Path) -> int:
    """Copy ``raw/app/`` objects onto a local raw root (``root/app/...``)."""

    s3 = client("s3", settings)
    prefix = "raw/app/"
    written = 0
    token: str | None = None
    while True:
        kwargs: dict[str, Any] = {"Bucket": settings.bucket, "Prefix": prefix}
        if token:
            kwargs["ContinuationToken"] = token
        try:
            page = s3.list_objects_v2(**kwargs)
        except ClientError as exc:
            if error_code(exc) in MISSING:
                return written
            raise
        for item in page.get("Contents", []):
            key = item["Key"]
            if not key.endswith(".parquet"):
                continue
            relative = key.removeprefix("raw/")
            dest = root / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            obj = s3.get_object(Bucket=settings.bucket, Key=key)
            dest.write_bytes(obj["Body"].read())
            written += 1
        if not page.get("IsTruncated"):
            return written
        token = page.get("NextContinuationToken")


def assert_current_state(settings: CdcSettings, report: LoadResult, root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    database = root.parent / "cdc.duckdb"
    build_warehouse(database, LocalRaw(root))
    con = duckdb.connect(str(database))
    try:
        for table, mart in _MART.items():
            actual = con.execute(f"select count(*) from marts.{mart}").fetchone()
            found = 0 if actual is None else int(actual[0])
            expected = _pg_count(settings.database_url, table)
            if found != expected:
                raise RuntimeError(f"{mart} has {found} rows, Postgres {table} has {expected}")
        status = con.execute(
            "select status from marts.cur_pix_key where id = ?",
            [report.updated_key_id],
        ).fetchone()
        if status is None or status[0] != report.updated_key_status:
            raise RuntimeError(
                f"updated key {report.updated_key_id} status is {status}, "
                f"expected {report.updated_key_status}"
            )
        for label, row_id, mart in (
            ("deleted key", report.deleted_key_id, "cur_pix_key"),
            ("deleted transaction", report.deleted_transaction_id, "cur_pix_transaction"),
        ):
            left = con.execute(
                f"select count(*) from marts.{mart} where id = ?",
                [row_id],
            ).fetchone()
            if left is None or int(left[0]) != 0:
                raise RuntimeError(f"{label} {row_id} is still in {mart}")
    finally:
        con.close()
    failed = [item for item in run_checks(database) if not item.ok]
    if failed:
        detail = ", ".join(f"{item.name}={item.violations}" for item in failed)
        raise RuntimeError(f"data-quality checks failed: {detail}")


def _pg_count(url: str, table: str) -> int:
    ident = quote_ident(table)
    with psycopg.connect(libpq_url(url)) as conn:
        row = conn.execute(f"SELECT count(*) FROM {ident}").fetchone()
    if row is None:
        return 0
    return int(row[0])
