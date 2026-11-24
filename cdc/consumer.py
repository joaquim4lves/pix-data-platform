"""Read pgoutput from a logical slot and publish envelopes to SQS.

``pg_logical_slot_peek_binary_changes`` does not move the slot. The slot
advances only after the envelopes for that commit are accepted by SQS.
A crash in between redelivers the same commits. The Parquet sink drops
the duplicates.

The slot sees WAL written after it was created. Rows that already existed
are not in the stream. ``make e2e`` creates the slot before it loads.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

import psycopg
from payments.settings import libpq_url

from cdc.decode import PgoutputDecoder
from cdc.envelope import events_from_transaction
from cdc.lsn import format_lsn, parse_lsn
from cdc.publish import SqsQueue
from cdc.settings import CdcSettings
from cdc.tables import APP_TABLES

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass(frozen=True)
class ConsumeResult:
    published: int
    advanced_to: str | None


def quote_ident(name: str) -> str:
    if not _IDENT.fullmatch(name):
        raise ValueError(f"refusing SQL identifier {name!r}")
    return name


def require_logical(conn: psycopg.Connection) -> None:
    level = conn.execute("SHOW wal_level").fetchone()
    current = "" if level is None else str(level[0])
    if current != "logical":
        raise RuntimeError(
            f"wal_level is {current!r}. pgoutput needs wal_level=logical. "
            "The compose file sets it; recreate the Postgres container so the "
            "setting is applied (it is read at server start)."
        )


def ensure_publication(conn: psycopg.Connection, name: str, tables: tuple[str, ...]) -> None:
    publication = quote_ident(name)
    quoted_tables = [quote_ident(table) for table in tables]
    found = conn.execute(
        "SELECT pubname FROM pg_publication WHERE pubname = %s",
        (name,),
    ).fetchone()
    if found is None:
        joined = ", ".join(quoted_tables)
        conn.execute(f"CREATE PUBLICATION {publication} FOR TABLE {joined}")
        return
    current = {
        str(row[0])
        for row in conn.execute(
            "SELECT tablename FROM pg_publication_tables WHERE pubname = %s",
            (name,),
        )
    }
    missing = [table for table in quoted_tables if table not in current]
    if missing:
        conn.execute(f"ALTER PUBLICATION {publication} ADD TABLE {', '.join(missing)}")


def ensure_slot(conn: psycopg.Connection, name: str) -> None:
    quote_ident(name)
    row = conn.execute(
        "SELECT plugin FROM pg_replication_slots WHERE slot_name = %s",
        (name,),
    ).fetchone()
    if row is None:
        conn.execute("SELECT pg_create_logical_replication_slot(%s, 'pgoutput')", (name,))
        return
    if row[0] != "pgoutput":
        raise RuntimeError(f"replication slot {name} uses plugin {row[0]!r}, not pgoutput")


def recreate_slot(conn: psycopg.Connection, name: str) -> None:
    quote_ident(name)
    row = conn.execute(
        "SELECT active FROM pg_replication_slots WHERE slot_name = %s",
        (name,),
    ).fetchone()
    if row is not None:
        if row[0]:
            raise RuntimeError(
                f"replication slot {name} is active. Stop the consumer before recreating it."
            )
        conn.execute("SELECT pg_drop_replication_slot(%s)", (name,))
    conn.execute("SELECT pg_create_logical_replication_slot(%s, 'pgoutput')", (name,))


def consume(settings: CdcSettings, *, once: bool = False, peek_limit: int = 500) -> ConsumeResult:
    queue = SqsQueue.from_settings(settings)
    published = 0
    advanced: str | None = None
    tables = tuple(APP_TABLES)
    with psycopg.connect(
        libpq_url(settings.database_url),
        autocommit=True,
        application_name="pix-cdc",
    ) as conn:
        require_logical(conn)
        ensure_publication(conn, settings.publication, tables)
        ensure_slot(conn, settings.slot)
        while True:
            transactions = _peek(conn, settings, peek_limit)
            if not transactions:
                if once:
                    return ConsumeResult(published, advanced)
                time.sleep(1)
                continue
            for txn in transactions:
                events = events_from_transaction(txn)
                queue.send(events)
                ack = format_lsn(txn.ack_lsn)
                conn.execute(
                    "SELECT pg_replication_slot_advance(%s, %s)",
                    (settings.slot, ack),
                )
                published += len(events)
                advanced = ack


def _peek(conn: psycopg.Connection, settings: CdcSettings, limit: int) -> list:
    """Return complete transactions. A commit past the peek window raises.

    Peeking a fixed count can slice a large transaction before its commit
    message. Advancing would skip the rest, so this retries with a wider
    window and refuses to pretend the slot is idle.
    """

    window = limit
    while True:
        rows = conn.execute(
            """
            SELECT lsn::text, data
            FROM pg_logical_slot_peek_binary_changes(
                %s,
                NULL,
                %s,
                'proto_version', '1',
                'publication_names', %s
            )
            """,
            (settings.slot, window, settings.publication),
        ).fetchall()
        decoder = PgoutputDecoder()
        transactions = []
        for lsn_text, data in rows:
            txn = decoder.feed(bytes(data), message_lsn=parse_lsn(str(lsn_text)))
            if txn is not None:
                transactions.append(txn)
        if transactions or not rows:
            return transactions
        if window >= 100_000:
            raise RuntimeError(
                "pgoutput peek contained no commit. One transaction is larger than "
                "100000 messages; load smaller batches or raise the peek limit."
            )
        window *= 4
