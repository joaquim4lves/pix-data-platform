"""pgoutput decoding and the committed-row envelope."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from cdc.decode import PgoutputDecoder, pg_timestamp
from cdc.envelope import events_from_transaction, partition_date
from cdc.lsn import format_lsn, lsn_sort_key
from tests.pgoutput_bytes import begin, commit, delete, insert, relation, update

KEY_COLUMNS = ("id", "key_type", "status", "updated_at")
OID = 16386


def _feed(messages: list[tuple[int, bytes]]):
    decoder = PgoutputDecoder()
    transactions = []
    for lsn, payload in messages:
        txn = decoder.feed(payload, message_lsn=lsn)
        if txn is not None:
            transactions.append(txn)
    return transactions


def _key_txn(*changes: tuple[int, bytes], end_lsn: int = 0x20, ts_us: int = 0):
    messages = [
        (0x10, begin(end_lsn, ts_us, 7)),
        (0x10, relation(OID, "public", "pix_keys", KEY_COLUMNS)),
        *changes,
        (end_lsn, commit(end_lsn, end_lsn, ts_us)),
    ]
    found = _feed(messages)
    assert len(found) == 1
    return found[0]


def test_lsn_sort_key_matches_numeric_order() -> None:
    assert format_lsn(0x19211C8) == "0/19211C8"
    ordered = ["0/9", "0/A", "0/10", "1/0"]
    assert sorted(ordered, key=lsn_sort_key) == ordered


def test_postgres_epoch_is_2000() -> None:
    assert pg_timestamp(0) == datetime(2000, 1, 1, tzinfo=UTC)


def test_insert_update_and_delete_round_trip() -> None:
    inserted = _key_txn((0x10, insert(OID, ["k1", "CPF", "active", "2026-11-24 12:00:00+00"])))
    events = events_from_transaction(inserted)
    assert len(events) == 1
    event = events[0]
    assert event.op == "insert"
    assert event.table == "pix_keys"
    assert event.pk == {"id": "k1"}
    assert event.before is None
    assert event.after is not None
    assert event.after["status"] == "active"
    assert event.after["updated_at"] == "2026-11-24T12:00:00.000000Z"
    assert event.lsn == "0/20"
    assert event.commit_ts == "2000-01-01T00:00:00.000000Z"

    changed = _key_txn(
        (
            0x10,
            update(
                OID,
                ["k1", "CPF", "active", "2026-11-24 12:00:00+00"],
                ["k1", "CPF", "inactive", "2026-11-24 13:00:00+00"],
            ),
        ),
        end_lsn=0x30,
    )
    updated = events_from_transaction(changed)[0]
    assert updated.op == "update"
    assert updated.before is not None and updated.before["status"] == "active"
    assert updated.after is not None and updated.after["status"] == "inactive"

    removed = _key_txn(
        (0x10, delete(OID, ["k1", "CPF", "inactive", "2026-11-24 13:00:00+00"], kind=b"K")),
        end_lsn=0x40,
    )
    deleted = events_from_transaction(removed)[0]
    assert deleted.op == "delete"
    assert deleted.after is None
    assert deleted.before is not None and deleted.before["id"] == "k1"


def test_same_transaction_collapses_to_the_committed_image() -> None:
    txn = _key_txn(
        (0x10, insert(OID, ["k1", "CPF", "active", None])),
        (
            0x18,
            update(
                OID,
                ["k1", "CPF", "active", None],
                ["k1", "CPF", "inactive", None],
            ),
        ),
    )
    events = events_from_transaction(txn)
    assert [(event.op, event.after["status"] if event.after else None) for event in events] == [
        ("insert", "inactive")
    ]

    vanished = _key_txn(
        (0x10, insert(OID, ["k1", "CPF", "active", None])),
        (0x18, delete(OID, ["k1", "CPF", "active", None])),
    )
    assert events_from_transaction(vanished) == []


def test_other_tables_are_ignored() -> None:
    messages = [
        (0x10, begin(0x20, 0, 1)),
        (0x10, relation(99, "public", "not_published", ("id",))),
        (0x10, insert(99, ["x"])),
        (0x20, commit(0x20, 0x20, 0)),
    ]
    assert events_from_transaction(_feed(messages)[0]) == []


def test_truncate_is_not_acknowledged() -> None:
    decoder = PgoutputDecoder()
    with pytest.raises(ValueError, match="truncate"):
        decoder.feed(b"T\x00\x00\x00\x01\x00", message_lsn=1)


def test_partition_date_uses_utc() -> None:
    assert partition_date("2026-11-24T23:30:00-03:00") == "2026-11-25"
    assert partition_date("2026-11-24T15:00:00.000000Z") == "2026-11-24"
