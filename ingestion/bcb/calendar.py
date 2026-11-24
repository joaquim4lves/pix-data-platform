"""Month arithmetic for PIX partitions.

The open month follows the calendar in America/Sao_Paulo. BCB publishes the
municipality series for the month that is still in progress, and that month
must not become the watermark.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

BRAZIL = ZoneInfo("America/Sao_Paulo")


def brazil_today(now: datetime | None = None) -> date:
    moment = now if now is not None else datetime.now(BRAZIL)
    if moment.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return moment.astimezone(BRAZIL).date()


def parse_ano_mes(value: int | str) -> int:
    text = str(value)
    if len(text) != 6 or not text.isdigit():
        raise ValueError(f"expected YYYYMM, got {value!r}")
    month = int(text[4:])
    if month < 1 or month > 12:
        raise ValueError(f"month out of range in {value!r}")
    return int(text)


def add_months(ano_mes: int, delta: int) -> int:
    ano_mes = parse_ano_mes(ano_mes)
    year, month = divmod(ano_mes, 100)
    index = year * 12 + (month - 1) + delta
    new_year, new_month_index = divmod(index, 12)
    return new_year * 100 + new_month_index + 1


def iter_months(start: int, end: int) -> list[int]:
    start = parse_ano_mes(start)
    end = parse_ano_mes(end)
    if start > end:
        raise ValueError(f"start {start} is after end {end}")
    months: list[int] = []
    year, month = divmod(start, 100)
    end_year, end_month = divmod(end, 100)
    while (year, month) <= (end_year, end_month):
        months.append(year * 100 + month)
        month += 1
        if month == 13:
            year += 1
            month = 1
    return months


def is_partial_month(ano_mes: int, today: date) -> bool:
    """A month that has not closed on ``today``, or any later month."""

    return parse_ano_mes(ano_mes) >= today.year * 100 + today.month


def month_start(ano_mes: int) -> date:
    ano_mes = parse_ano_mes(ano_mes)
    year, month = divmod(ano_mes, 100)
    return date(year, month, 1)


def next_month_start(ano_mes: int) -> date:
    return month_start(add_months(ano_mes, 1))


@dataclass(frozen=True)
class FetchPlan:
    months: tuple[int, ...]
    partial_months: tuple[int, ...]


def plan_incremental(*, today: date, lookback: int, watermark: int | None) -> FetchPlan:
    """Last ``lookback`` months, plus a catch-up when the watermark is older.

    The current calendar month is included so an open municipality month is
    reprocessed. It is listed in ``partial_months`` and must not be checkpointed.
    """

    if lookback < 1:
        raise ValueError("lookback must be >= 1")
    current = today.year * 100 + today.month
    window_start = add_months(current, -(lookback - 1))
    start = window_start
    if watermark is not None:
        watermark = parse_ano_mes(watermark)
        if add_months(watermark, 1) < window_start:
            start = add_months(watermark, -(lookback - 1))
    months = tuple(iter_months(start, current))
    partial = tuple(month for month in months if is_partial_month(month, today))
    return FetchPlan(months=months, partial_months=partial)


def plan_backfill(start: int, end: int, *, today: date) -> FetchPlan:
    months = tuple(iter_months(start, end))
    partial = tuple(month for month in months if is_partial_month(month, today))
    return FetchPlan(months=months, partial_months=partial)


def advance_watermark(
    previous: int | None,
    written: Iterable[int],
    partial: Iterable[int],
) -> int | None:
    """Move the checkpoint forward to the newest closed month actually written.

    Partial months are ignored. The checkpoint never moves backward, so a later
    empty response cannot forget a month that was already stored.
    """

    partial_set = {parse_ano_mes(month) for month in partial}
    complete = [
        parse_ano_mes(month) for month in written if parse_ano_mes(month) not in partial_set
    ]
    if not complete:
        return previous
    candidate = max(complete)
    if previous is None:
        return candidate
    return max(parse_ano_mes(previous), candidate)


def utc_now() -> datetime:
    return datetime.now(UTC)
