"""Choose an incremental ingest or an AnoMes backfill for one DAG run.

A scheduled run uses the ingestion watermark and the lookback window. That is
the same contract as ``make ingest`` and the EventBridge Lambda. A historical
month is explicit: DAG conf ``start``/``end`` or ``ano_mes``, or an Airflow
backfill run whose logical date is that month in America/Sao_Paulo.

``catchup=True`` on the timetable does not by itself select old months. Those
runs are scheduled runs, and a scheduled run revises the recent window. Replay
history with conf, or with ``airflow dags backfill``, which sets the run type
this module treats as one AnoMes per logical date.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from ingestion.bcb.calendar import BRAZIL, parse_ano_mes


@dataclass(frozen=True)
class IngestPlan:
    mode: str
    start: int | None = None
    end: int | None = None
    lookback_months: int | None = None


def resolve_ingest_plan(
    *,
    conf: Mapping[str, object] | None,
    run_type: object,
    logical_date: datetime | None,
) -> IngestPlan:
    payload = dict(conf or {})
    start = _optional_month(payload.get("start"), field="start")
    end = _optional_month(payload.get("end"), field="end")
    if (start is None) ^ (end is None):
        raise ValueError("backfill conf requires both start and end as YYYYMM")
    if start is not None and end is not None:
        if start > end:
            raise ValueError(f"start {start} is after end {end}")
        return IngestPlan(mode="backfill", start=start, end=end)

    ano_mes = _optional_month(payload.get("ano_mes"), field="ano_mes")
    if ano_mes is not None:
        return IngestPlan(mode="backfill", start=ano_mes, end=ano_mes)

    if _run_type(run_type) == "backfill":
        if logical_date is None:
            raise ValueError("a backfill run needs a logical date to derive AnoMes")
        month = logical_ano_mes(logical_date)
        return IngestPlan(mode="backfill", start=month, end=month)

    lookback = _optional_int(payload.get("lookback_months"), field="lookback_months")
    if lookback is not None and lookback < 1:
        raise ValueError("lookback_months must be >= 1")
    return IngestPlan(mode="ingest", lookback_months=lookback)


def logical_ano_mes(moment: datetime) -> int:
    """YYYYMM of ``moment`` on the BCB calendar (America/Sao_Paulo)."""

    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    local = moment.astimezone(BRAZIL)
    return local.year * 100 + local.month


def _run_type(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw).lower()


def _optional_month(value: object, *, field: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        return parse_ano_mes(value if isinstance(value, int | str) else str(value))
    except ValueError as exc:
        raise ValueError(f"{field} must be YYYYMM, got {value!r}") from exc


def _optional_int(value: object, *, field: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, int | str):
        raise ValueError(f"{field} must be an integer, got {value!r}")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an integer, got {value!r}") from exc
