"""Model SQL stays in the subset Athena and Trino share with DuckDB."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL_ROOTS = (
    ROOT / "transform" / "sql",
    ROOT / "transform" / "dbt" / "models",
    ROOT / "transform" / "dbt" / "tests",
    ROOT / "docs" / "queries",
)
FORBIDDEN = (
    "read_parquet",
    "hive_partitioning",
    "QUALIFY",
    "GROUP BY ALL",
    "strftime",
    "strptime",
    "date_add",
    "list_transform",
    "unnest(",
    "epoch_ms",
    "generate_series",
)


def test_sql_files_avoid_duckdb_only_syntax() -> None:
    files = [path for root in SQL_ROOTS if root.exists() for path in root.rglob("*.sql")]
    assert files, "expected SQL models under transform/sql"
    offenders: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)} contains {token}")
    assert offenders == []
