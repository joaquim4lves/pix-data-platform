"""Minimal pgoutput encoder for decoder tests. Not used in production."""

from __future__ import annotations

import struct


def _u64(value: int) -> bytes:
    return struct.pack("!Q", value)


def _i32(value: int) -> bytes:
    return struct.pack("!i", value)


def _i16(value: int) -> bytes:
    return struct.pack("!h", value)


def _cstr(value: str) -> bytes:
    return value.encode() + b"\x00"


def begin(final_lsn: int, ts_us: int, xid: int) -> bytes:
    return b"B" + _u64(final_lsn) + _u64(ts_us) + _i32(xid)


def commit(commit_lsn: int, end_lsn: int, ts_us: int, flags: int = 0) -> bytes:
    return b"C" + struct.pack("!B", flags) + _u64(commit_lsn) + _u64(end_lsn) + _u64(ts_us)


def relation(oid: int, namespace: str, name: str, columns: tuple[str, ...]) -> bytes:
    body = b"R" + _i32(oid) + _cstr(namespace) + _cstr(name)
    body += struct.pack("!B", ord("f")) + _i16(len(columns))
    for column in columns:
        body += struct.pack("!B", 1) + _cstr(column) + _i32(25) + _i32(-1)
    return body


def tuple_data(values: list[str | None]) -> bytes:
    body = _i16(len(values))
    for value in values:
        if value is None:
            body += b"n"
            continue
        raw = value.encode()
        body += b"t" + _i32(len(raw)) + raw
    return body


def insert(oid: int, values: list[str | None]) -> bytes:
    return b"I" + _i32(oid) + b"N" + tuple_data(values)


def update(
    oid: int,
    old: list[str | None],
    new: list[str | None],
    *,
    old_kind: bytes = b"O",
) -> bytes:
    return b"U" + _i32(oid) + old_kind + tuple_data(old) + b"N" + tuple_data(new)


def delete(oid: int, old: list[str | None], *, kind: bytes = b"O") -> bytes:
    return b"D" + _i32(oid) + kind + tuple_data(old)
