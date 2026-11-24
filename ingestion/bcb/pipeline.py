"""Incremental and backfill runs.

Each entity is independent. A contract failure quarantines the raw response
and stops that entity without moving its watermark. Other entities still run.
An empty month is left untouched: BCB publishes some series late, and an empty
body must not delete a partition that was written earlier.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, ValidationError

from ingestion.bcb.calendar import (
    advance_watermark,
    brazil_today,
    plan_backfill,
    plan_incremental,
    utc_now,
)
from ingestion.bcb.client import OlindaClient, Page
from ingestion.bcb.entities import ENTITIES, ENTITY_ORDER, EntitySpec
from ingestion.bcb.errors import OlindaError, PayloadError
from ingestion.bcb.settings import Settings
from ingestion.bcb.store import ObjectStore

logger = logging.getLogger("ingestion.bcb.pipeline")


@dataclass
class EntityRun:
    entity: str
    ok: bool
    rows_written: int
    rows_by_month: dict[int, int]
    watermark: int | None
    error: str | None = None
    quarantined_keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "entity": self.entity,
            "ok": self.ok,
            "rows_written": self.rows_written,
            "rows_by_month": {str(month): count for month, count in self.rows_by_month.items()},
            "watermark": self.watermark,
            "error": self.error,
            "quarantined_keys": list(self.quarantined_keys),
        }


@dataclass
class RunResult:
    entities: list[EntityRun]

    @property
    def ok(self) -> bool:
        return all(item.ok for item in self.entities)

    def to_dict(self) -> dict[str, object]:
        return {"ok": self.ok, "entities": [item.to_dict() for item in self.entities]}


def select_entities(names: list[str] | None) -> list[EntitySpec]:
    if not names:
        return list(ENTITY_ORDER)
    selected: list[EntitySpec] = []
    for name in names:
        try:
            selected.append(ENTITIES[name])
        except KeyError as exc:
            known = ", ".join(ENTITIES)
            raise ValueError(f"unknown entity {name!r}; known: {known}") from exc
    return selected


def run(
    settings: Settings,
    *,
    mode: str,
    lookback_months: int | None = None,
    start: int | None = None,
    end: int | None = None,
    entities: list[str] | None = None,
    now: datetime | None = None,
    client: OlindaClient | None = None,
    store: ObjectStore | None = None,
) -> RunResult:
    if mode not in {"ingest", "backfill"}:
        raise ValueError(f"unknown mode {mode!r}")
    moment = now or utc_now()
    today = brazil_today(moment)
    lookback = settings.lookback_months if lookback_months is None else lookback_months
    if mode == "ingest" and lookback < 1:
        raise ValueError("lookback_months must be >= 1")
    if mode == "backfill" and (start is None or end is None):
        raise ValueError("backfill requires start and end")

    owned_client = client is None
    if client is None:
        client = OlindaClient(
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
            max_retries=settings.max_retries,
            backoff_seconds=settings.backoff_seconds,
            page_size=settings.page_size,
        )
    if store is None:
        store = ObjectStore.from_settings(settings)
        store.ensure_bucket()

    try:
        watermarks = store.load_watermarks()
        results: list[EntityRun] = []
        for spec in select_entities(entities):
            previous = watermarks.get(spec.name)
            if mode == "ingest":
                plan = plan_incremental(today=today, lookback=lookback, watermark=previous)
            else:
                assert start is not None and end is not None
                plan = plan_backfill(start, end, today=today)
            logger.info(
                "planned entity",
                extra={
                    "entity": spec.name,
                    "mode": mode,
                    "months": list(plan.months),
                    "partial_months": list(plan.partial_months),
                    "watermark": previous,
                },
            )
            results.append(
                _run_entity(
                    spec,
                    plan.months,
                    set(plan.partial_months),
                    previous,
                    moment,
                    client,
                    store,
                )
            )
        return RunResult(entities=results)
    finally:
        if owned_client:
            client.close()


def _run_entity(
    spec: EntitySpec,
    months: tuple[int, ...],
    partial: set[int],
    previous: int | None,
    moment: datetime,
    client: OlindaClient,
    store: ObjectStore,
) -> EntityRun:
    rows_by_month: dict[int, int] = {}
    written: list[int] = []
    quarantined: list[str] = []
    for month in months:
        try:
            pages = client.fetch_month(spec, month)
            validated = _validate(spec, month, pages, store, moment, quarantined)
        except (OlindaError, PayloadError, ValidationError) as exc:
            if isinstance(exc, PayloadError):
                quarantined.append(store.put_quarantine(spec.name, month, exc.body, now=moment))
            return _failed(spec, rows_by_month, previous, exc, quarantined)
        rows_by_month[month] = len(validated)
        if not validated:
            logger.info(
                "month has no rows",
                extra={"entity": spec.name, "ano_mes": month},
            )
            continue
        store.write_partition(spec, month, validated)
        written.append(month)
        logger.info(
            "wrote partition",
            extra={"entity": spec.name, "ano_mes": month, "rows": len(validated)},
        )

    watermark = advance_watermark(previous, written, partial)
    if watermark is not None and watermark != previous:
        store.save_watermark(spec.name, watermark, moment)
    return EntityRun(
        entity=spec.name,
        ok=True,
        rows_written=sum(rows_by_month.values()),
        rows_by_month=rows_by_month,
        watermark=watermark,
        quarantined_keys=quarantined,
    )


def _validate(
    spec: EntitySpec,
    month: int,
    pages: list[Page],
    store: ObjectStore,
    moment: datetime,
    quarantined: list[str],
) -> list[BaseModel]:
    validated: list[BaseModel] = []
    for page in pages:
        page_rows: list[BaseModel] = []
        for index, row in enumerate(page.rows):
            try:
                page_rows.append(spec.model.model_validate(row))
            except ValidationError as exc:
                key = store.put_quarantine(spec.name, month, page.body, now=moment)
                quarantined.append(key)
                logger.error(
                    "payload failed contract",
                    extra={
                        "entity": spec.name,
                        "ano_mes": month,
                        "row_index": index,
                        "quarantine_key": key,
                        "errors": exc.error_count(),
                    },
                )
                raise
        validated.extend(page_rows)
    return validated


def _failed(
    spec: EntitySpec,
    rows_by_month: dict[int, int],
    previous: int | None,
    exc: Exception,
    quarantined: list[str],
) -> EntityRun:
    logger.error(
        "entity failed",
        extra={"entity": spec.name, "error": str(exc), "quarantined_keys": quarantined},
    )
    return EntityRun(
        entity=spec.name,
        ok=False,
        rows_written=sum(rows_by_month.values()),
        rows_by_month=rows_by_month,
        watermark=previous,
        error=str(exc),
        quarantined_keys=quarantined,
    )
