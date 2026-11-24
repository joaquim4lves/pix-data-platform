"""Drain the CDC queue into the Parquet sink.

Successes are deleted. Failures stay invisible until the visibility timeout
and are counted so the command can exit non-zero. The Lambda handler reports
the same split through ``batchItemFailures`` and lets the event source
mapping delete the successes.
"""

from __future__ import annotations

from dataclasses import dataclass

from cdc.handler import handler
from cdc.publish import SqsQueue
from cdc.settings import CdcSettings


@dataclass(frozen=True)
class ApplyResult:
    deleted: int
    failed: int


def apply_queue(
    settings: CdcSettings,
    *,
    wait_seconds: int = 1,
    max_batches: int = 100,
) -> ApplyResult:
    queue = SqsQueue.from_settings(settings)
    deleted = 0
    failed = 0
    wait = wait_seconds
    for _ in range(max_batches):
        messages = queue.receive(wait_seconds=wait)
        if not messages:
            return ApplyResult(deleted, failed)
        result = handler({"Records": messages}, None)
        failed_ids = {item["itemIdentifier"] for item in result["batchItemFailures"]}
        ok = [item for item in messages if item["messageId"] not in failed_ids]
        queue.delete(ok)
        deleted += len(ok)
        failed += len(failed_ids)
        wait = 0
    raise RuntimeError("SQS drain hit the batch limit while messages were still arriving")
