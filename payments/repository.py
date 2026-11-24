"""Writes shared by the API and the load generator."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from payments.models import PixDispute, PixKey, PixTransaction
from payments.schemas import (
    PixDisputeCreate,
    PixDisputeUpdate,
    PixKeyCreate,
    PixKeyUpdate,
    PixTransactionCreate,
    PixTransactionUpdate,
)


def create_key(db: Session, payload: PixKeyCreate) -> PixKey:
    now = datetime.now(UTC)
    row = PixKey(id=uuid.uuid4(), created_at=now, updated_at=now, **payload.model_dump())
    db.add(row)
    db.flush()
    return row


def update_key(db: Session, row: PixKey, payload: PixKeyUpdate) -> PixKey:
    _apply(row, payload)
    db.flush()
    return row


def create_transaction(db: Session, payload: PixTransactionCreate) -> PixTransaction:
    now = datetime.now(UTC)
    row = PixTransaction(id=uuid.uuid4(), created_at=now, updated_at=now, **payload.model_dump())
    db.add(row)
    db.flush()
    return row


def update_transaction(
    db: Session,
    row: PixTransaction,
    payload: PixTransactionUpdate,
) -> PixTransaction:
    _apply(row, payload)
    db.flush()
    return row


def create_dispute(db: Session, payload: PixDisputeCreate) -> PixDispute:
    now = datetime.now(UTC)
    row = PixDispute(id=uuid.uuid4(), created_at=now, updated_at=now, **payload.model_dump())
    db.add(row)
    db.flush()
    return row


def update_dispute(db: Session, row: PixDispute, payload: PixDisputeUpdate) -> PixDispute:
    _apply(row, payload)
    db.flush()
    return row


def list_keys(
    db: Session,
    *,
    status: str | None,
    ispb: str | None,
    limit: int,
    offset: int,
) -> tuple[list[PixKey], int]:
    return _page(db, PixKey, status=status, ispb=ispb, limit=limit, offset=offset)


def list_transactions(
    db: Session,
    *,
    status: str | None,
    limit: int,
    offset: int,
) -> tuple[list[PixTransaction], int]:
    return _page(db, PixTransaction, status=status, ispb=None, limit=limit, offset=offset)


def list_disputes(
    db: Session,
    *,
    status: str | None,
    limit: int,
    offset: int,
) -> tuple[list[PixDispute], int]:
    return _page(db, PixDispute, status=status, ispb=None, limit=limit, offset=offset)


def _apply(row: PixKey | PixTransaction | PixDispute, payload: BaseModel) -> None:
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return
    for key, value in data.items():
        setattr(row, key, value)
    row.updated_at = datetime.now(UTC)


def _page(
    db: Session,
    model: type[PixKey] | type[PixTransaction] | type[PixDispute],
    *,
    status: str | None,
    ispb: str | None,
    limit: int,
    offset: int,
) -> tuple[list, int]:
    query = select(model)
    counted = select(func.count()).select_from(model)
    if status is not None:
        query = query.where(model.status == status)
        counted = counted.where(model.status == status)
    if ispb is not None and model is PixKey:
        query = query.where(PixKey.ispb == ispb)
        counted = counted.where(PixKey.ispb == ispb)
    total = int(db.scalar(counted) or 0)
    rows = list(db.scalars(query.order_by(model.created_at, model.id).limit(limit).offset(offset)))
    return rows, total
