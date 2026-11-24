"""Deterministic-enough load of inserts, updates, and deletes.

Each change is its own commit so the replication slot sees one envelope
per change. ``reset`` deletes existing rows the same way. TRUNCATE is not
used: the consumer refuses a truncate message, and a truncate would not
leave a delete event for each primary key.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from payments.db import session_factory
from payments.models import PixDispute, PixKey, PixTransaction
from payments.repository import (
    create_dispute,
    create_key,
    create_transaction,
    update_dispute,
    update_key,
    update_transaction,
)
from payments.schemas import (
    PixDisputeCreate,
    PixDisputeUpdate,
    PixKeyCreate,
    PixKeyUpdate,
    PixTransactionCreate,
    PixTransactionUpdate,
)

ISPBS = (
    "00000000",
    "60701190",
    "60746948",
    "00360305",
    "90400888",
    "05938780",
)
# 3550308 and 2103406 are in the v0.2 fixture warehouse (São Paulo, Coelho Neto).
MUNICIPIOS = (3550308, 3304557, 2927408, 2304400, 4106902, 4314902, 5300108, 2103406)
OUR_ISPB = "05938780"


@dataclass
class LoadResult:
    inserted: dict[str, int] = field(
        default_factory=lambda: {"pix_keys": 0, "pix_transactions": 0, "pix_disputes": 0}
    )
    updated: dict[str, int] = field(
        default_factory=lambda: {"pix_keys": 0, "pix_transactions": 0, "pix_disputes": 0}
    )
    deleted: dict[str, int] = field(
        default_factory=lambda: {"pix_keys": 0, "pix_transactions": 0, "pix_disputes": 0}
    )
    updated_key_id: str = ""
    updated_key_status: str = "inactive"
    deleted_key_id: str = ""
    deleted_transaction_id: str = ""
    kept_key_id: str = ""

    def operation_count(self) -> int:
        return sum(self.inserted.values()) + sum(self.updated.values()) + sum(self.deleted.values())


def load_operational(
    url: str,
    *,
    seed: int = 7,
    keys: int = 12,
    transactions: int = 20,
    disputes: int = 6,
    reset: bool = False,
) -> LoadResult:
    if keys < 2 or transactions < 1 or disputes < 1:
        raise ValueError("load needs at least 2 keys, 1 transaction, and 1 dispute")
    rng = random.Random(seed)
    started = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
    db = session_factory(url)()
    result = LoadResult()
    try:
        if reset:
            result.deleted["pix_disputes"] += _delete_all(db, PixDispute)
            result.deleted["pix_transactions"] += _delete_all(db, PixTransaction)
            result.deleted["pix_keys"] += _delete_all(db, PixKey)
        key_rows = [_insert_key(db, rng, index) for index in range(keys)]
        result.inserted["pix_keys"] += len(key_rows)
        payment_rows = [
            _insert_transaction(db, rng, index, started) for index in range(transactions)
        ]
        extra = _insert_transaction(db, rng, transactions, started)
        result.inserted["pix_transactions"] += len(payment_rows) + 1
        dispute_rows = [
            _insert_dispute(db, rng, payment_rows[index % len(payment_rows)], index, started)
            for index in range(disputes)
        ]
        result.inserted["pix_disputes"] += len(dispute_rows)

        updated = update_key(db, key_rows[0], PixKeyUpdate(status="inactive"))
        db.commit()
        result.updated["pix_keys"] += 1
        result.updated_key_id = str(updated.id)
        result.kept_key_id = str(updated.id)

        update_transaction(db, payment_rows[0], PixTransactionUpdate(status="refunded"))
        db.commit()
        result.updated["pix_transactions"] += 1

        update_dispute(
            db,
            dispute_rows[0],
            PixDisputeUpdate(status="accepted", resolved_at=started + timedelta(hours=5)),
        )
        db.commit()
        result.updated["pix_disputes"] += 1

        deleted_key = key_rows[1]
        result.deleted_key_id = str(deleted_key.id)
        db.delete(deleted_key)
        db.commit()
        result.deleted["pix_keys"] += 1

        result.deleted_transaction_id = str(extra.id)
        db.delete(extra)
        db.commit()
        result.deleted["pix_transactions"] += 1

        if len(dispute_rows) > 1:
            db.delete(dispute_rows[-1])
            db.commit()
            result.deleted["pix_disputes"] += 1
        return result
    finally:
        db.close()


def _insert_key(db: Session, rng: random.Random, index: int) -> PixKey:
    person = "PJ" if index % 5 == 0 else "PF"
    if person == "PJ":
        key_type = rng.choice(("CNPJ", "e-mail", "Aleatória"))
    else:
        key_type = rng.choice(("CPF", "Celular", "e-mail", "Aleatória"))
    row = create_key(
        db,
        PixKeyCreate(
            key_type=key_type,
            key_value=_key_value(key_type, uuid.uuid4()),
            person_type=person,
            ispb=rng.choice(ISPBS),
            municipio_ibge=rng.choice(MUNICIPIOS),
            status="active",
        ),
    )
    db.commit()
    return row


def _insert_transaction(
    db: Session,
    rng: random.Random,
    index: int,
    started: datetime,
) -> PixTransaction:
    when = started + timedelta(minutes=index)
    direction = "outbound" if index % 2 == 0 else "inbound"
    payer = OUR_ISPB if direction == "outbound" else rng.choice(ISPBS)
    receiver = rng.choice(ISPBS) if direction == "outbound" else OUR_ISPB
    row_id = uuid.uuid4()
    amount = (Decimal(rng.randrange(100, 250_000)) / Decimal(100)).quantize(Decimal("0.01"))
    row = create_transaction(
        db,
        PixTransactionCreate(
            end_to_end_id=_end_to_end(payer, row_id.hex, when),
            amount=amount,
            payer_ispb=payer,
            receiver_ispb=receiver,
            municipio_ibge=rng.choice(MUNICIPIOS),
            forma_iniciacao=rng.choice(("DICT", "MANU", "QRES", "QRDN", "INIC", "AUTO")),
            direction=direction,
            status="settled",
            occurred_at=when,
        ),
    )
    db.commit()
    return row


def _insert_dispute(
    db: Session,
    rng: random.Random,
    payment: PixTransaction,
    index: int,
    started: datetime,
) -> PixDispute:
    row = create_dispute(
        db,
        PixDisputeCreate(
            transaction_id=payment.id,
            reason=rng.choice(("scam", "unauthorized", "operational_failure")),
            status="open",
            opened_at=started + timedelta(hours=1, minutes=index),
        ),
    )
    db.commit()
    return row


def _delete_all(db: Session, model: type[PixDispute] | type[PixTransaction] | type[PixKey]) -> int:
    rows = list(db.scalars(select(model)))
    for row in rows:
        db.delete(row)
        db.commit()
    return len(rows)


def _key_value(key_type: str, row_id: uuid.UUID) -> str:
    number = int(row_id.hex[:16], 16)
    if key_type == "CPF":
        return f"{number % 10**11:011d}"
    if key_type == "CNPJ":
        return f"{number % 10**14:014d}"
    if key_type == "Celular":
        return f"+55119{number % 10**8:08d}"
    if key_type == "e-mail":
        return f"user-{row_id.hex[:12]}@example.test"
    if key_type == "Aleatória":
        return str(row_id)
    raise ValueError(key_type)


def _end_to_end(ispb: str, unique: str, when: datetime) -> str:
    body = f"E{ispb}{when.strftime('%Y%m%d%H%M')}{unique[:11].upper()}"
    if len(body) != 32:
        raise RuntimeError(f"end-to-end id must be 32 characters, got {body!r}")
    return body
