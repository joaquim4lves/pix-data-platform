"""Decode pgoutput bytes into committed transactions.

The message layouts are the logical replication protocol documented for
Postgres 16. Tuple values stay in the text form the plugin emits. The
envelope layer turns a transaction into one event per primary key.

A truncate stops the consumer. Acknowledging it would drop every row
without a delete event, and the current-state model would keep the ghosts.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

PG_EPOCH = datetime(2000, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class PgChange:
    op: str
    schema: str
    table: str
    before: dict[str, str | None] | None
    after: dict[str, str | None] | None


@dataclass(frozen=True)
class PgTransaction:
    xid: int
    commit_lsn: int
    ack_lsn: int
    commit_ts: datetime
    changes: tuple[PgChange, ...]


@dataclass(frozen=True)
class _Column:
    name: str


@dataclass
class _Relation:
    oid: int
    namespace: str
    name: str
    columns: tuple[_Column, ...]


class _Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def _need(self, size: int) -> None:
        if self.pos + size > len(self.data):
            raise ValueError("truncated pgoutput message")

    def u8(self) -> int:
        self._need(1)
        value = self.data[self.pos]
        self.pos += 1
        return value

    def i16(self) -> int:
        self._need(2)
        value = struct.unpack_from("!h", self.data, self.pos)[0]
        self.pos += 2
        return value

    def i32(self) -> int:
        self._need(4)
        value = struct.unpack_from("!i", self.data, self.pos)[0]
        self.pos += 4
        return value

    def u64(self) -> int:
        self._need(8)
        value = struct.unpack_from("!Q", self.data, self.pos)[0]
        self.pos += 8
        return value

    def cstr(self) -> str:
        end = self.data.find(b"\x00", self.pos)
        if end < 0:
            raise ValueError("truncated pgoutput string")
        value = self.data[self.pos : end].decode("utf-8")
        self.pos = end + 1
        return value

    def bytes(self, size: int) -> bytes:
        self._need(size)
        value = self.data[self.pos : self.pos + size]
        self.pos += size
        return value


def pg_timestamp(microseconds: int) -> datetime:
    return PG_EPOCH + timedelta(microseconds=microseconds)


class PgoutputDecoder:
    def __init__(self) -> None:
        self._relations: dict[int, _Relation] = {}
        self._xid: int | None = None
        self._changes: list[PgChange] = []

    def feed(self, payload: bytes, *, message_lsn: int) -> PgTransaction | None:
        if not payload:
            raise ValueError("empty pgoutput message")
        tag = chr(payload[0])
        reader = _Reader(payload)
        reader.u8()
        txn = self._dispatch(tag, reader, message_lsn)
        if reader.pos != len(payload):
            extra = len(payload) - reader.pos
            raise ValueError(f"pgoutput message {tag} has {extra} trailing bytes")
        return txn

    def _dispatch(self, tag: str, reader: _Reader, message_lsn: int) -> PgTransaction | None:
        if tag == "B":
            self._begin(reader)
            return None
        if tag == "C":
            return self._commit(reader, message_lsn)
        if tag == "R":
            self._relation(reader)
            return None
        if tag == "I":
            self._insert(reader)
            return None
        if tag == "U":
            self._update(reader)
            return None
        if tag == "D":
            self._delete(reader)
            return None
        if tag == "Y":
            self._skip_type(reader)
            return None
        if tag == "O":
            self._skip_origin(reader)
            return None
        if tag == "M":
            self._skip_message(reader)
            return None
        if tag == "T":
            raise ValueError("pgoutput truncate is not applied; refusing to advance the slot")
        raise ValueError(f"unsupported pgoutput message {tag!r}")

    def _begin(self, reader: _Reader) -> None:
        if self._xid is not None:
            raise ValueError("pgoutput begin while a transaction is open")
        reader.u64()
        reader.u64()
        self._xid = reader.i32()
        self._changes = []

    def _commit(self, reader: _Reader, message_lsn: int) -> PgTransaction:
        if self._xid is None:
            raise ValueError("pgoutput commit without begin")
        reader.u8()
        reader.u64()
        end_lsn = reader.u64()
        commit_ts = pg_timestamp(reader.u64())
        txn = PgTransaction(
            xid=self._xid,
            commit_lsn=end_lsn,
            ack_lsn=max(message_lsn, end_lsn),
            commit_ts=commit_ts,
            changes=tuple(self._changes),
        )
        self._xid = None
        self._changes = []
        return txn

    def _relation(self, reader: _Reader) -> None:
        oid = reader.i32()
        namespace = reader.cstr()
        name = reader.cstr()
        reader.u8()
        count = reader.i16()
        columns: list[_Column] = []
        for _ in range(count):
            reader.u8()
            column = reader.cstr()
            reader.i32()
            reader.i32()
            columns.append(_Column(column))
        self._relations[oid] = _Relation(oid, namespace, name, tuple(columns))

    def _insert(self, reader: _Reader) -> None:
        relation = self._relation_for(reader.i32())
        marker = chr(reader.u8())
        if marker != "N":
            raise ValueError(f"insert tuple marker {marker!r}")
        self._append("insert", relation, None, _tuple_dict(reader, relation))

    def _update(self, reader: _Reader) -> None:
        relation = self._relation_for(reader.i32())
        marker = chr(reader.u8())
        before = None
        if marker in {"K", "O"}:
            before = _tuple_dict(reader, relation)
            marker = chr(reader.u8())
        if marker != "N":
            raise ValueError(f"update tuple marker {marker!r}")
        self._append("update", relation, before, _tuple_dict(reader, relation))

    def _delete(self, reader: _Reader) -> None:
        relation = self._relation_for(reader.i32())
        marker = chr(reader.u8())
        if marker not in {"K", "O"}:
            raise ValueError(f"delete tuple marker {marker!r}")
        self._append("delete", relation, _tuple_dict(reader, relation), None)

    def _append(
        self,
        op: str,
        relation: _Relation,
        before: dict[str, str | None] | None,
        after: dict[str, str | None] | None,
    ) -> None:
        if self._xid is None:
            raise ValueError(f"pgoutput {op} outside a transaction")
        self._changes.append(
            PgChange(
                op=op,
                schema=relation.namespace,
                table=relation.name,
                before=before,
                after=after,
            )
        )

    def _relation_for(self, oid: int) -> _Relation:
        try:
            return self._relations[oid]
        except KeyError as exc:
            raise ValueError(f"pgoutput change for unknown relation oid {oid}") from exc

    def _skip_type(self, reader: _Reader) -> None:
        reader.i32()
        reader.cstr()
        reader.cstr()

    def _skip_origin(self, reader: _Reader) -> None:
        reader.u64()
        reader.cstr()

    def _skip_message(self, reader: _Reader) -> None:
        reader.u8()
        reader.u64()
        reader.cstr()
        size = reader.i32()
        if size < 0:
            raise ValueError("negative logical message length")
        reader.bytes(size)


def _tuple_dict(reader: _Reader, relation: _Relation) -> dict[str, str | None]:
    count = reader.i16()
    if count != len(relation.columns):
        raise ValueError(
            f"{relation.name} tuple has {count} columns, relation has {len(relation.columns)}"
        )
    values: dict[str, str | None] = {}
    for column in relation.columns:
        marker = chr(reader.u8())
        if marker == "n":
            values[column.name] = None
        elif marker == "u":
            raise ValueError(f"unchanged TOAST value in {relation.name}.{column.name}")
        elif marker == "t":
            length = reader.i32()
            if length < 0:
                raise ValueError("negative tuple length")
            values[column.name] = reader.bytes(length).decode("utf-8")
        else:
            raise ValueError(f"tuple marker {marker!r}")
    return values
