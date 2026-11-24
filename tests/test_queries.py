"""Example questions in docs/queries run on the fixture warehouse."""

from decimal import Decimal
from pathlib import Path

import duckdb
from tests.pix_warehouse import build_sample

ROOT = Path(__file__).resolve().parents[1]
QUERIES = ROOT / "docs" / "queries"


def _money(value: object) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def test_example_queries_answer_the_fixture(tmp_path: Path) -> None:
    database = build_sample(tmp_path)
    con = duckdb.connect(str(database))

    volume = con.execute((QUERIES / "pix_volume_by_month.sql").read_text()).fetchall()
    assert [(row[0], _money(row[1]), _money(row[2])) for row in volume] == [
        (202402, Decimal("4.00"), Decimal("1.00")),
        (202609, Decimal("9.00"), Decimal("2.00")),
        (202610, Decimal("18.00"), Decimal("5.00")),
    ]

    ufs = con.execute((QUERIES / "top_ufs_by_value_received.sql").read_text()).fetchall()
    assert [row[0] for row in ufs] == ["SP", "MA"]
    assert _money(ufs[0][2]) == Decimal("1500.00")
    assert "Não informado" not in {row[1] for row in ufs}

    cities = con.execute((QUERIES / "top_municipios_by_value_received.sql").read_text()).fetchall()
    assert [row[0] for row in cities] == ["SAO PAULO", "COELHO NETO"]
    assert _money(cities[0][2]) == Decimal("1500.00")
    assert "Não informado" not in {row[0] for row in cities}

    mix = con.execute((QUERIES / "key_type_mix.sql").read_text()).fetchall()
    assert [(row[0], row[2]) for row in mix] == [("CPF", 10), ("Celular", 4), ("e-mail", 2)]
    con.close()
