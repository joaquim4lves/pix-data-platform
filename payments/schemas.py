"""Pydantic request and response models for the operational API."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from payments.models import (
    DIRECTIONS,
    DISPUTE_REASONS,
    DISPUTE_STATUSES,
    INITIATION_FORMS,
    KEY_STATUSES,
    KEY_TYPES,
    PERSON_TYPES,
    TRANSACTION_STATUSES,
)

KeyType = Literal["CPF", "CNPJ", "Celular", "e-mail", "Aleatória"]
PersonType = Literal["PF", "PJ"]
KeyStatus = Literal["active", "inactive"]
Direction = Literal["outbound", "inbound"]
InitiationForm = Literal["DICT", "MANU", "INIC", "QRES", "QRDN", "AUTO", "APDN", "APES"]
TransactionStatus = Literal["pending", "settled", "rejected", "refunded"]
DisputeReason = Literal["scam", "unauthorized", "operational_failure"]
DisputeStatus = Literal["open", "accepted", "rejected"]


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return value


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PixKeyCreate(ApiModel):
    key_type: KeyType
    key_value: str = Field(min_length=1, max_length=77)
    person_type: PersonType
    ispb: str = Field(pattern=r"^\d{8}$")
    municipio_ibge: int = Field(ge=0, le=9_999_999)
    status: KeyStatus = "active"


class PixKeyUpdate(ApiModel):
    key_type: KeyType | None = None
    key_value: str | None = Field(default=None, min_length=1, max_length=77)
    person_type: PersonType | None = None
    ispb: str | None = Field(default=None, pattern=r"^\d{8}$")
    municipio_ibge: int | None = Field(default=None, ge=0, le=9_999_999)
    status: KeyStatus | None = None


class PixKeyRead(ApiModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: uuid.UUID
    key_type: KeyType
    key_value: str
    person_type: PersonType
    ispb: str
    municipio_ibge: int
    status: KeyStatus
    created_at: datetime
    updated_at: datetime


class PixTransactionCreate(ApiModel):
    end_to_end_id: str = Field(pattern=r"^E[A-Za-z0-9]{31}$")
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    payer_ispb: str = Field(pattern=r"^\d{8}$")
    receiver_ispb: str = Field(pattern=r"^\d{8}$")
    municipio_ibge: int = Field(ge=0, le=9_999_999)
    forma_iniciacao: InitiationForm
    direction: Direction
    status: TransactionStatus = "pending"
    occurred_at: datetime

    def model_post_init(self, _context: object) -> None:
        _aware(self.occurred_at)


class PixTransactionUpdate(ApiModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=18, decimal_places=2)
    status: TransactionStatus | None = None


class PixTransactionRead(ApiModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: uuid.UUID
    end_to_end_id: str
    amount: Decimal
    payer_ispb: str
    receiver_ispb: str
    municipio_ibge: int
    forma_iniciacao: InitiationForm
    direction: Direction
    status: TransactionStatus
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime


class PixDisputeCreate(ApiModel):
    transaction_id: uuid.UUID
    reason: DisputeReason
    status: DisputeStatus = "open"
    opened_at: datetime
    resolved_at: datetime | None = None

    def model_post_init(self, _context: object) -> None:
        _aware(self.opened_at)
        if self.resolved_at is not None:
            _aware(self.resolved_at)


class PixDisputeUpdate(ApiModel):
    reason: DisputeReason | None = None
    status: DisputeStatus | None = None
    resolved_at: datetime | None = None


class PixDisputeRead(ApiModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: uuid.UUID
    transaction_id: uuid.UUID
    reason: DisputeReason
    status: DisputeStatus
    opened_at: datetime
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class KeyPage(ApiModel):
    items: list[PixKeyRead]
    total: int
    limit: int
    offset: int


class TransactionPage(ApiModel):
    items: list[PixTransactionRead]
    total: int
    limit: int
    offset: int


class DisputePage(ApiModel):
    items: list[PixDisputeRead]
    total: int
    limit: int
    offset: int


def _assert_codes() -> None:
    """Keep the schema literals aligned with the database checks."""

    assert set(KEY_TYPES) == set(KeyType.__args__)
    assert set(PERSON_TYPES) == set(PersonType.__args__)
    assert set(KEY_STATUSES) == set(KeyStatus.__args__)
    assert set(DIRECTIONS) == set(Direction.__args__)
    assert set(INITIATION_FORMS) == set(InitiationForm.__args__)
    assert set(TRANSACTION_STATUSES) == set(TransactionStatus.__args__)
    assert set(DISPUTE_REASONS) == set(DisputeReason.__args__)
    assert set(DISPUTE_STATUSES) == set(DisputeStatus.__args__)


_assert_codes()
