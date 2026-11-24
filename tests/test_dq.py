"""Data-quality checks fail when the fixture violates a rule."""

from pathlib import Path

import duckdb
from ingestion.bcb.entities import TRANSACOES
from tests.pix_warehouse import build_sample, write_sample_raw
from tests.raw_files import write_partition
from tests.samples import tx_row
from transform.build import build_warehouse
from transform.checks import run_checks
from transform.sources import LocalRaw


def _by_name(database: Path) -> dict[str, int]:
    return {item.name: item.violations for item in run_checks(database)}


def test_sample_warehouse_passes_every_check(tmp_path: Path) -> None:
    database = build_sample(tmp_path)
    violations = _by_name(database)
    assert violations
    assert set(violations.values()) == {0}


def test_negative_amount_fails_the_non_negative_check(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    write_partition(
        raw,
        TRANSACOES,
        202610,
        [tx_row(AnoMes=202610, VALOR="-1.00", QUANTIDADE=1)],
    )
    database = tmp_path / "pix.duckdb"
    build_warehouse(database, LocalRaw(raw))
    violations = _by_name(database)
    assert violations["fct_transacoes_mensal_non_negative"] == 1
    assert violations["fct_transacoes_mensal_unique_grain"] == 0


def test_duplicate_grain_fails_the_uniqueness_check(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    write_partition(
        raw,
        TRANSACOES,
        202610,
        [
            tx_row(AnoMes=202610, VALOR="1.00", QUANTIDADE=1),
            tx_row(AnoMes=202610, VALOR="2.00", QUANTIDADE=4),
        ],
    )
    database = tmp_path / "pix.duckdb"
    build_warehouse(database, LocalRaw(raw))
    violations = _by_name(database)
    assert violations["fct_transacoes_mensal_unique_grain"] == 1


def test_missing_dimension_row_fails_referential_integrity(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    write_sample_raw(raw)
    database = tmp_path / "pix.duckdb"
    build_warehouse(database, LocalRaw(raw))
    con = duckdb.connect(str(database))
    con.execute("delete from marts.dim_natureza where codigo = 'P2P'")
    con.close()
    violations = _by_name(database)
    assert violations["fct_transacoes_mensal_references"] >= 1
