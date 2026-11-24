"""Run the SQL data-quality checks against a built warehouse.

Each file in ``transform/sql/checks`` is a SELECT that returns one row per
violation. An empty result passes. ``make dq`` and the pytest suite call
the same function.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

SQL_DIR = Path(__file__).resolve().parent / "sql" / "checks"


@dataclass(frozen=True)
class CheckResult:
    name: str
    violations: int

    @property
    def ok(self) -> bool:
        return self.violations == 0


def run_checks(database: Path) -> list[CheckResult]:
    database = Path(database)
    if not database.exists():
        raise FileNotFoundError(f"warehouse not found: {database}. Run make model first.")
    paths = sorted(SQL_DIR.glob("*.sql"))
    if not paths:
        raise FileNotFoundError(f"no data-quality checks in {SQL_DIR}")
    con = duckdb.connect(str(database), read_only=True)
    try:
        results: list[CheckResult] = []
        for path in paths:
            try:
                rows = con.execute(path.read_text(encoding="utf-8")).fetchall()
            except duckdb.Error as exc:
                raise RuntimeError(f"{path} failed: {exc}") from exc
            results.append(CheckResult(path.stem, len(rows)))
        return results
    finally:
        con.close()
