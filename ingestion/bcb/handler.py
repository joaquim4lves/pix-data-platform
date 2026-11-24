"""Lambda-style entrypoint.

Event shape::

    {"mode": "ingest", "lookback_months": 3, "entities": ["ChavesPix"]}
    {"mode": "backfill", "start": 202011, "end": 202012}

A failed entity raises ``IngestionError`` so the invocation is marked failed.
Successful entities in the same event are already committed; a retry rewrites
those partitions.
"""

from __future__ import annotations

import json
import os
from typing import Any

from ingestion.bcb.errors import IngestionError
from ingestion.bcb.logging import configure_logging
from ingestion.bcb.pipeline import run
from ingestion.bcb.settings import Settings


def handler(event: dict[str, Any] | None, context: object) -> dict[str, Any]:
    del context
    configure_logging(os.environ.get("LOG_LEVEL", "INFO"))
    payload = event or {}
    settings = Settings.from_env()
    entities = payload.get("entities")
    if isinstance(entities, str):
        entities = [part.strip() for part in entities.split(",") if part.strip()]
    result = run(
        settings,
        mode=str(payload.get("mode", "ingest")),
        lookback_months=payload.get("lookback_months"),
        start=_optional_int(payload.get("start")),
        end=_optional_int(payload.get("end")),
        entities=entities,
    )
    body = result.to_dict()
    if not result.ok:
        raise IngestionError(json.dumps(body))
    return body


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, int | str):
        raise ValueError(f"expected YYYYMM, got {value!r}")
    return int(value)
