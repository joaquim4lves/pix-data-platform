from datetime import UTC, date, datetime

import pytest
from ingestion.bcb.calendar import (
    add_months,
    advance_watermark,
    brazil_today,
    is_partial_month,
    parse_ano_mes,
    plan_backfill,
    plan_incremental,
)


def test_add_months_crosses_year_boundaries() -> None:
    assert add_months(202012, 1) == 202101
    assert add_months(202601, -2) == 202511
    assert add_months(202611, -2) == 202609


def test_parse_ano_mes_rejects_bad_months() -> None:
    with pytest.raises(ValueError):
        parse_ano_mes("202613")
    with pytest.raises(ValueError):
        parse_ano_mes("20261")


def test_open_month_follows_sao_paulo() -> None:
    now = datetime(2026, 12, 1, 1, 30, tzinfo=UTC)
    today = brazil_today(now)
    assert today == date(2026, 11, 30)
    assert is_partial_month(202611, today)
    assert not is_partial_month(202610, today)


def test_incremental_window_includes_the_open_month() -> None:
    plan = plan_incremental(today=date(2026, 11, 24), lookback=3, watermark=None)
    assert plan.months == (202609, 202610, 202611)
    assert plan.partial_months == (202611,)


def test_caught_up_watermark_does_not_widen_the_window() -> None:
    plan = plan_incremental(today=date(2026, 11, 24), lookback=3, watermark=202610)
    assert plan.months == (202609, 202610, 202611)


def test_stale_watermark_catches_up_and_revises_the_lookback() -> None:
    plan = plan_incremental(today=date(2026, 11, 24), lookback=3, watermark=202601)
    assert plan.months[0] == 202511
    assert plan.months[-1] == 202611
    assert 202602 in plan.months


def test_backfill_marks_the_open_month_and_rejects_an_inverted_range() -> None:
    plan = plan_backfill(202610, 202611, today=date(2026, 11, 24))
    assert plan.months == (202610, 202611)
    assert plan.partial_months == (202611,)
    with pytest.raises(ValueError):
        plan_backfill(202612, 202601, today=date(2026, 11, 24))


def test_watermark_ignores_a_partial_month_and_does_not_move_backward() -> None:
    assert advance_watermark(None, [202609, 202610, 202611], [202611]) == 202610
    assert advance_watermark(202610, [202609], []) == 202610
    assert advance_watermark(None, [202611], [202611]) is None
