"""Lambda-style SQS consumer that lands CDC events as Parquet.

Event shape::

    {"Records": [{"messageId": "...", "body": "{...envelope...}"}]}

A record whose body is not a valid envelope is reported in
``batchItemFailures`` and is not written. The other records in the batch
still land. If the object write itself fails, every record that was going
into that write is reported, so the source retries them. A repeated
``lsn`` + primary key is a success with no new row: the sink already has it.

The function does not delete SQS messages. Lambda's event source mapping
does that from ``batchItemFailures``. ``python -m cdc apply`` deletes the
successes itself.
"""

from __future__ import annotations

from typing import Any

from cdc.envelope import ChangeEvent
from cdc.settings import CdcSettings
from cdc.sink import CdcSink


def handler(event: dict[str, Any] | None, context: object) -> dict[str, Any]:
    del context
    records = (event or {}).get("Records") or []
    failures: list[str] = []
    parsed: list[tuple[str, ChangeEvent]] = []
    for record in records:
        message_id = str(record.get("messageId", ""))
        try:
            parsed.append((message_id, ChangeEvent.from_json(record.get("body", ""))))
        except (TypeError, ValueError):
            failures.append(message_id)
    if parsed:
        try:
            CdcSink.from_settings(CdcSettings.from_env()).write([event for _, event in parsed])
        except Exception:
            failures.extend(message_id for message_id, _ in parsed)
    return {"batchItemFailures": [{"itemIdentifier": message_id} for message_id in failures]}
