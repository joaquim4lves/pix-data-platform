"""Slot lag and the quarantine prefix.

An idle logical slot pins WAL. The lag check is the alert for that, not a
second consumer. A missing slot is logged: ``make cdc`` creates it, and a
quiet laptop often has none. Lag above ``AIRFLOW_VAR_CDC_SLOT_LAG_BYTES``
(fallback ``CDC_SLOT_LAG_BYTES``, default 256 MiB) fails the task.

Quarantine objects mean a payload broke the contract and the watermark did
not move. Any key under ``quarantine/`` fails the task.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from ingestion.bcb.settings import Settings
from ingestion.bcb.store import ObjectStore

from orchestration.alerts import notify

DEFAULT_SLOT_LAG_BYTES = 256 * 1024 * 1024


@dataclass(frozen=True)
class SlotLag:
    slot: str
    exists: bool
    active: bool
    lag_bytes: int | None


class SlotLagError(RuntimeError):
    """The replication slot is holding more WAL than the configured limit."""


class QuarantinePresentError(RuntimeError):
    """The raw zone has at least one quarantined payload."""


def slot_lag_limit() -> int:
    raw = os.environ.get("AIRFLOW_VAR_CDC_SLOT_LAG_BYTES") or os.environ.get("CDC_SLOT_LAG_BYTES")
    if raw is None or raw.strip() == "":
        return DEFAULT_SLOT_LAG_BYTES
    try:
        limit = int(raw)
    except ValueError as exc:
        raise ValueError(f"CDC slot lag limit must be an integer byte count, got {raw!r}") from exc
    if limit < 0:
        raise ValueError("CDC slot lag limit must be >= 0")
    return limit


def read_slot_lag(conn: object, slot: str) -> SlotLag:
    cursor = conn.execute(  # type: ignore[attr-defined]
        """
        SELECT slot_name,
               active,
               pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn)
        FROM pg_replication_slots
        WHERE slot_name = %s
        """,
        (slot,),
    )
    row = cursor.fetchone()
    if row is None:
        return SlotLag(slot=slot, exists=False, active=False, lag_bytes=None)
    lag = row[2]
    return SlotLag(
        slot=str(row[0]),
        exists=True,
        active=bool(row[1]),
        lag_bytes=None if lag is None else int(lag),
    )


def enforce_slot_lag(report: SlotLag) -> dict[str, object]:
    limit = slot_lag_limit()
    payload: dict[str, object] = {
        "slot": report.slot,
        "exists": report.exists,
        "active": report.active,
        "lag_bytes": report.lag_bytes,
        "limit_bytes": limit,
    }
    if not report.exists:
        notify("slot_missing", f"replication slot {report.slot} does not exist")
        return payload
    if report.lag_bytes is not None and report.lag_bytes > limit:
        notify(
            "slot_lag",
            f"slot {report.slot} lag_bytes={report.lag_bytes} limit_bytes={limit}",
        )
        raise SlotLagError(f"slot {report.slot} lag {report.lag_bytes} bytes exceeds {limit}")
    return payload


def report_slot_lag() -> dict[str, object]:
    import psycopg
    from cdc.settings import CdcSettings
    from payments.settings import libpq_url

    settings = CdcSettings.from_env()
    with psycopg.connect(libpq_url(settings.database_url), autocommit=True) as conn:
        report = read_slot_lag(conn, settings.slot)
    return enforce_slot_lag(report)


def quarantine_keys(store: ObjectStore) -> list[str]:
    return store.list_keys("quarantine/")


def enforce_quarantine(store: ObjectStore) -> dict[str, object]:
    keys = quarantine_keys(store)
    if keys:
        notify("quarantine", f"{len(keys)} quarantined payloads in {store.bucket}")
        raise QuarantinePresentError(f"{len(keys)} quarantined objects in {store.bucket}")
    return {"bucket": store.bucket, "keys": []}


def report_quarantine() -> dict[str, object]:
    store = ObjectStore.from_settings(Settings.from_env())
    return enforce_quarantine(store)
