"""SQLAlchemy models for the simulated PSP.

The codes that also exist in the v0.2 warehouse use the same literals:
ISPB is 8 digits, ``municipio_ibge`` is the IBGE municipality code,
``key_type`` matches ``dim_tipo_chave``, and ``forma_iniciacao`` matches
``dim_forma_iniciacao``. Disputes are a small stand-in for MED, not the
BCB fraud extract.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

KEY_TYPES = ("CPF", "CNPJ", "Celular", "e-mail", "Aleatória")
PERSON_TYPES = ("PF", "PJ")
KEY_STATUSES = ("active", "inactive")
DIRECTIONS = ("outbound", "inbound")
INITIATION_FORMS = ("DICT", "MANU", "INIC", "QRES", "QRDN", "AUTO", "APDN", "APES")
TRANSACTION_STATUSES = ("pending", "settled", "rejected", "refunded")
DISPUTE_REASONS = ("scam", "unauthorized", "operational_failure")
DISPUTE_STATUSES = ("open", "accepted", "rejected")


class Base(DeclarativeBase):
    pass


def _in(column: str, values: tuple[str, ...]) -> str:
    quoted = ", ".join("'" + value.replace("'", "''") + "'" for value in values)
    return f"{column} in ({quoted})"


class PixKey(Base):
    __tablename__ = "pix_keys"
    __table_args__ = (
        CheckConstraint(_in("key_type", KEY_TYPES), name="ck_pix_keys_key_type"),
        CheckConstraint(_in("person_type", PERSON_TYPES), name="ck_pix_keys_person_type"),
        CheckConstraint(_in("status", KEY_STATUSES), name="ck_pix_keys_status"),
        CheckConstraint("ispb ~ '^[0-9]{8}$'", name="ck_pix_keys_ispb"),
        CheckConstraint(
            "municipio_ibge >= 0 and municipio_ibge <= 9999999",
            name="ck_pix_keys_municipio",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    key_type: Mapped[str] = mapped_column(String(16))
    key_value: Mapped[str] = mapped_column(String(77), unique=True)
    person_type: Mapped[str] = mapped_column(String(2))
    ispb: Mapped[str] = mapped_column(String(8))
    municipio_ibge: Mapped[int]
    status: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PixTransaction(Base):
    __tablename__ = "pix_transactions"
    __table_args__ = (
        CheckConstraint(_in("direction", DIRECTIONS), name="ck_pix_transactions_direction"),
        CheckConstraint(
            _in("forma_iniciacao", INITIATION_FORMS),
            name="ck_pix_transactions_forma",
        ),
        CheckConstraint(
            _in("status", TRANSACTION_STATUSES),
            name="ck_pix_transactions_status",
        ),
        CheckConstraint("payer_ispb ~ '^[0-9]{8}$'", name="ck_pix_transactions_payer_ispb"),
        CheckConstraint("receiver_ispb ~ '^[0-9]{8}$'", name="ck_pix_transactions_receiver_ispb"),
        CheckConstraint("amount > 0", name="ck_pix_transactions_amount"),
        CheckConstraint(
            "municipio_ibge >= 0 and municipio_ibge <= 9999999",
            name="ck_pix_transactions_municipio",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    end_to_end_id: Mapped[str] = mapped_column(String(32), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    payer_ispb: Mapped[str] = mapped_column(String(8))
    receiver_ispb: Mapped[str] = mapped_column(String(8))
    municipio_ibge: Mapped[int]
    forma_iniciacao: Mapped[str] = mapped_column(String(16))
    direction: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PixDispute(Base):
    __tablename__ = "pix_disputes"
    __table_args__ = (
        CheckConstraint(_in("reason", DISPUTE_REASONS), name="ck_pix_disputes_reason"),
        CheckConstraint(_in("status", DISPUTE_STATUSES), name="ck_pix_disputes_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pix_transactions.id"),
        index=True,
    )
    reason: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
