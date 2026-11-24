"""Current-state merge over a CDC Parquet log. No Docker."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import duckdb
from cdc.envelope import ChangeEvent
from cdc.sink import arrow_table, parquet_bytes
from cdc.tables import APP_TABLES
from tests.pix_warehouse import write_sample_raw
from transform.build import build_warehouse
from transform.checks import run_checks
from transform.sources import LocalRaw, app_parquet_glob

ROOT = Path(__file__).resolve().parents[1]


def _image(table: str, **values: str | None) -> dict[str, str | None]:
    return {column: values.get(column) for column in APP_TABLES[table].columns}


def _event(
    table: str,
    op: str,
    lsn: str,
    row_id: str,
    *,
    before: dict[str, str | None] | None = None,
    after: dict[str, str | None] | None = None,
    commit_ts: str = "2026-11-24T15:00:00.000000Z",
) -> ChangeEvent:
    return ChangeEvent(
        op=op,
        table=table,
        pk={"id": row_id},
        before=before,
        after=after,
        lsn=lsn,
        commit_ts=commit_ts,
    )


def _write(root: Path, name: str, events: list[ChangeEvent]) -> None:
    grouped: dict[str, list[ChangeEvent]] = {}
    for event in events:
        grouped.setdefault(event.table, []).append(event)
    for table, batch in grouped.items():
        path = root / "app" / table / "dt=2026-11-24" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(parquet_bytes(arrow_table(APP_TABLES[table], batch)))


def test_latest_lsn_wins_and_deletes_drop_out(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    write_sample_raw(raw)
    assert app_parquet_glob(LocalRaw(raw), "pix_keys").endswith("app/pix_keys/dt=*/*.parquet")

    key_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    key_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    base = {
        "key_type": "CPF",
        "key_value": "10000000001",
        "person_type": "PF",
        "ispb": "5938780",
        "municipio_ibge": "3550308",
        "created_at": "2026-11-24T12:00:00.000000Z",
        "updated_at": "2026-11-24T12:00:00.000000Z",
    }
    active = _image("pix_keys", id=key_a, status="active", **base)
    inactive = _image("pix_keys", id=key_a, status="inactive", **base)
    other = _image(
        "pix_keys",
        id=key_b,
        status="active",
        key_value="10000000002",
        **{k: v for k, v in base.items() if k != "key_value"},
    )
    payment_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    removed_payment = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    payment = _image(
        "pix_transactions",
        id=payment_id,
        end_to_end_id="E0593878020261124120000000000001",
        amount="10.50",
        payer_ispb="05938780",
        receiver_ispb="00000000",
        municipio_ibge="3550308",
        forma_iniciacao="DICT",
        direction="outbound",
        status="settled",
        occurred_at="2026-11-24T12:00:00.000000Z",
        created_at="2026-11-24T12:00:00.000000Z",
        updated_at="2026-11-24T12:00:00.000000Z",
    )
    refunded = {**payment, "status": "refunded"}
    dropped = {
        **payment,
        "id": removed_payment,
        "end_to_end_id": "E0593878020261124120000000000002",
    }
    dispute = _image(
        "pix_disputes",
        id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
        transaction_id=payment_id,
        reason="scam",
        status="open",
        opened_at="2026-11-24T13:00:00.000000Z",
        resolved_at=None,
        created_at="2026-11-24T13:00:00.000000Z",
        updated_at="2026-11-24T13:00:00.000000Z",
    )
    # The higher LSN is written first so file order cannot win.
    _write(
        raw,
        "part-late.parquet",
        [
            _event("pix_keys", "update", "0/30", key_a, before=active, after=inactive),
            _event("pix_keys", "delete", "0/40", key_b, before=other),
            _event(
                "pix_transactions",
                "update",
                "0/22",
                payment_id,
                before=payment,
                after=refunded,
            ),
            _event("pix_transactions", "delete", "0/23", removed_payment, before=dropped),
        ],
    )
    _write(
        raw,
        "part-early.parquet",
        [
            _event("pix_keys", "insert", "0/10", key_a, after=active),
            _event("pix_keys", "insert", "0/15", key_b, after=other),
            _event("pix_transactions", "insert", "0/16", payment_id, after=payment),
            _event("pix_transactions", "insert", "0/17", removed_payment, after=dropped),
            _event("pix_disputes", "insert", "0/18", dispute["id"] or "", after=dispute),
        ],
    )

    database = tmp_path / "pix.duckdb"
    build_warehouse(database, LocalRaw(raw))
    con = duckdb.connect(str(database))
    keys = {
        row[0]: row
        for row in con.execute(
            "select id, status, ispb, municipio_ibge from marts.cur_pix_key"
        ).fetchall()
    }
    assert set(keys) == {key_a}
    assert keys[key_a][1:] == ("inactive", "05938780", 3550308)
    payment_row = con.execute("select status, amount from marts.cur_pix_transaction").fetchone()
    assert payment_row is not None
    assert payment_row[0] == "refunded"
    assert Decimal(str(payment_row[1])) == Decimal("10.50")
    assert con.execute("select count(*) from marts.cur_pix_transaction").fetchone() == (1,)
    assert con.execute("select transaction_id, reason from marts.cur_pix_dispute").fetchone() == (
        payment_id,
        "scam",
    )
    query = (ROOT / "docs/queries/app_keys_by_municipality.sql").read_text()
    cities = con.execute(query).fetchall()
    assert cities == [("SAO PAULO", "SP", 1)]
    con.close()
    assert set(item.violations for item in run_checks(database)) == {0}
