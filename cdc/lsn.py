"""WAL positions as Postgres prints them, and a key that sorts the same way.

``0/A`` is less than ``0/10``. A fixed-width uppercase hex string matches
that order; the raw display form does not, because its width varies.
"""

from __future__ import annotations


def format_lsn(value: int) -> str:
    if value < 0:
        raise ValueError(f"LSN must be >= 0, got {value}")
    return f"{value >> 32:X}/{value & 0xFFFFFFFF:X}"


def parse_lsn(text: str) -> int:
    try:
        high, low = text.split("/")
        value = (int(high, 16) << 32) | int(low, 16)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"invalid LSN {text!r}") from exc
    if value < 0:
        raise ValueError(f"invalid LSN {text!r}")
    return value


def lsn_sort_key(text: str) -> str:
    return f"{parse_lsn(text):016X}"
