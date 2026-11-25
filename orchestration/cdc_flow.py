"""Drain the local logical slot into SQS and the Parquet sink.

This is the laptop path. In AWS the event source mapping invokes the sink
Lambda, and this function is not deployed there. ``consume(..., once=True)``
publishes whatever the slot has not advanced past, then ``apply_queue`` writes
Parquet and deletes the successes. A failed message stays on the queue and
fails the task so Airflow retries the drain.
"""

from __future__ import annotations

from cdc.apply import apply_queue
from cdc.consumer import consume
from cdc.settings import CdcSettings


def drain_cdc() -> dict[str, object]:
    settings = CdcSettings.from_env()
    consumed = consume(settings, once=True)
    applied = apply_queue(settings)
    if applied.failed:
        raise RuntimeError(f"CDC sink left {applied.failed} messages on {settings.queue_name}")
    return {
        "published": consumed.published,
        "advanced_to": consumed.advanced_to,
        "deleted": applied.deleted,
        "failed": applied.failed,
    }
