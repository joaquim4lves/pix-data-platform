"""One Olinda entity per task, using the v0.1 pipeline.

The client already retries HTTP 429 and 500. The task retries again with
exponential backoff when that budget is spent, or when the entity is
quarantined. A retry rewrites the same partitions. The watermark does not
advance on a failed entity.
"""

from __future__ import annotations

import json

from ingestion.bcb.entities import ENTITY_ORDER
from ingestion.bcb.errors import IngestionError
from ingestion.bcb.pipeline import run
from ingestion.bcb.settings import Settings

from orchestration.windows import IngestPlan


def bcb_entity_names() -> list[str]:
    return [spec.name for spec in ENTITY_ORDER]


def ingest_entity(entity: str, plan: IngestPlan) -> dict[str, object]:
    if plan.mode not in {"ingest", "backfill"}:
        raise ValueError(f"unknown mode {plan.mode!r}")
    settings = Settings.from_env()
    result = run(
        settings,
        mode=plan.mode,
        lookback_months=plan.lookback_months,
        start=plan.start,
        end=plan.end,
        entities=[entity],
    )
    body = result.to_dict()
    if not result.ok:
        raise IngestionError(json.dumps(body))
    return body
