"""Logical replication through SQS into the current-state tables.

Needs Postgres with wal_level=logical. SQS and S3 are moto, so LocalStack
is not required. CI's Postgres service is not logical, and this skips there.
"""

from __future__ import annotations

import psycopg
import pytest
from cdc.pipeline import assert_current_state, run_pipeline, sync_app_parquet
from cdc.settings import CdcSettings
from moto import mock_aws
from payments.settings import database_url, libpq_url, with_database

pytestmark = pytest.mark.integration


def test_slot_load_and_merge(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    admin = database_url()
    try:
        with psycopg.connect(libpq_url(admin), autocommit=True, connect_timeout=2) as conn:
            conn.execute("select 1")
            level = conn.execute("show wal_level").fetchone()
            if level is None or level[0] != "logical":
                pytest.skip(f"wal_level is {None if level is None else level[0]}")
            found = conn.execute(
                "select 1 from pg_database where datname = 'pix_cdc_itest'"
            ).fetchone()
            if found is None:
                conn.execute("create database pix_cdc_itest")
    except Exception as exc:
        pytest.skip(f"Postgres is not available: {exc}")

    url = with_database(admin, "pix_cdc_itest")
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("AWS_ENDPOINT_URL", "")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("S3_BUCKET", "pix-cdc-itest")
    monkeypatch.setenv("CDC_PUBLICATION", "pix_itest_pub")
    monkeypatch.setenv("CDC_SLOT", "pix_itest_slot")
    monkeypatch.setenv("CDC_QUEUE", "pix-cdc-itest")
    settings = CdcSettings.from_env()
    try:
        with mock_aws():
            result = run_pipeline(
                settings,
                reset=True,
                seed=3,
                keys=4,
                transactions=3,
                disputes=2,
                apply_wait=0,
            )
            root = tmp_path / "raw"
            assert sync_app_parquet(settings, root) > 0
            assert_current_state(settings, result.load, root)
    finally:
        with psycopg.connect(libpq_url(url), autocommit=True) as conn:
            row = conn.execute(
                "select active from pg_replication_slots where slot_name = 'pix_itest_slot'"
            ).fetchone()
            if row is not None and not row[0]:
                conn.execute("select pg_drop_replication_slot('pix_itest_slot')")
