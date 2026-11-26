"""The versioned Metabase files match the dashboard contract."""

from __future__ import annotations

from dashboards.validate import problems


def test_dashboard_definitions_match_the_contract() -> None:
    assert problems() == []
