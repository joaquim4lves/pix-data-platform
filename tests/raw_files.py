"""Write small raw Parquet partitions with the ingestion encoder.

Tests build these files on disk and point the warehouse at them, so the
suite never calls Olinda or S3.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
from ingestion.bcb.entities import EntitySpec
from ingestion.bcb.store import _table


def write_partition(
    root: Path,
    spec: EntitySpec,
    ano_mes: int,
    rows: list[dict[str, object]],
) -> None:
    models = [spec.model.model_validate(row) for row in rows]
    table = _table(spec, models)
    path = root / "bcb" / spec.name / f"ano_mes={ano_mes}" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, compression="snappy")
