"""FastAPI surface for the simulated PSP.

``/docs`` and ``/openapi.json`` are the generated contract. Writes commit
once per request, which is the transaction logical replication will see.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from payments.db import make_engine
from payments.models import PixDispute, PixKey, PixTransaction
from payments.repository import (
    create_dispute,
    create_key,
    create_transaction,
    list_disputes,
    list_keys,
    list_transactions,
    update_dispute,
    update_key,
    update_transaction,
)
from payments.schemas import (
    DisputePage,
    KeyPage,
    PixDisputeCreate,
    PixDisputeRead,
    PixDisputeUpdate,
    PixKeyCreate,
    PixKeyRead,
    PixKeyUpdate,
    PixTransactionCreate,
    PixTransactionRead,
    PixTransactionUpdate,
    TransactionPage,
)
from payments.settings import database_url


def get_db(request: Request) -> Generator[Session, None, None]:
    db = request.app.state.session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


Db = Annotated[Session, Depends(get_db)]
Limit = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0)]
Ispb = Annotated[str | None, Query(pattern=r"^\d{8}$")]
RowModel = type[PixKey] | type[PixTransaction] | type[PixDispute]


def create_app(url: str | None = None) -> FastAPI:
    app = FastAPI(
        title="PIX operational API",
        version="0.3.0",
        summary="Simulated PSP registry for PIX keys, transactions, and disputes.",
    )
    engine = make_engine(url or database_url())
    app.state.engine = engine
    app.state.session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    app.include_router(_routes())
    return app


def _routes():
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/health")
    def health(db: Db) -> dict[str, str]:
        try:
            db.execute(text("select 1"))
        except SQLAlchemyError as exc:
            raise HTTPException(status_code=503, detail="database unavailable") from exc
        return {"status": "ok"}

    @router.post("/keys", response_model=PixKeyRead, status_code=201)
    def post_key(payload: PixKeyCreate, db: Db) -> PixKey:
        try:
            return create_key(db, payload)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail=_conflict(exc)) from exc

    @router.get("/keys", response_model=KeyPage)
    def get_keys(
        db: Db,
        status: str | None = None,
        ispb: Ispb = None,
        limit: Limit = 50,
        offset: Offset = 0,
    ) -> KeyPage:
        rows, total = list_keys(db, status=status, ispb=ispb, limit=limit, offset=offset)
        return KeyPage(
            items=[PixKeyRead.model_validate(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    @router.get("/keys/{key_id}", response_model=PixKeyRead)
    def get_key(key_id: uuid.UUID, db: Db) -> PixKey:
        return _get(db, PixKey, key_id)

    @router.patch("/keys/{key_id}", response_model=PixKeyRead)
    def patch_key(
        key_id: uuid.UUID,
        payload: PixKeyUpdate,
        db: Db,
    ) -> PixKey:
        row = _get(db, PixKey, key_id)
        try:
            return update_key(db, row, payload)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail=_conflict(exc)) from exc

    @router.delete("/keys/{key_id}", status_code=204)
    def delete_key(key_id: uuid.UUID, db: Db) -> None:
        db.delete(_get(db, PixKey, key_id))

    @router.post("/transactions", response_model=PixTransactionRead, status_code=201)
    def post_transaction(
        payload: PixTransactionCreate,
        db: Db,
    ) -> PixTransaction:
        try:
            return create_transaction(db, payload)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail=_conflict(exc)) from exc

    @router.get("/transactions", response_model=TransactionPage)
    def get_transactions(
        db: Db,
        status: str | None = None,
        limit: Limit = 50,
        offset: Offset = 0,
    ) -> TransactionPage:
        rows, total = list_transactions(db, status=status, limit=limit, offset=offset)
        return TransactionPage(
            items=[PixTransactionRead.model_validate(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    @router.get("/transactions/{transaction_id}", response_model=PixTransactionRead)
    def get_transaction(
        transaction_id: uuid.UUID,
        db: Db,
    ) -> PixTransaction:
        return _get(db, PixTransaction, transaction_id)

    @router.patch("/transactions/{transaction_id}", response_model=PixTransactionRead)
    def patch_transaction(
        transaction_id: uuid.UUID,
        payload: PixTransactionUpdate,
        db: Db,
    ) -> PixTransaction:
        return update_transaction(db, _get(db, PixTransaction, transaction_id), payload)

    @router.delete("/transactions/{transaction_id}", status_code=204)
    def delete_transaction(transaction_id: uuid.UUID, db: Db) -> None:
        try:
            db.delete(_get(db, PixTransaction, transaction_id))
            db.flush()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail=_conflict(exc)) from exc

    @router.post("/disputes", response_model=PixDisputeRead, status_code=201)
    def post_dispute(payload: PixDisputeCreate, db: Db) -> PixDispute:
        try:
            return create_dispute(db, payload)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail=_conflict(exc)) from exc

    @router.get("/disputes", response_model=DisputePage)
    def get_disputes(
        db: Db,
        status: str | None = None,
        limit: Limit = 50,
        offset: Offset = 0,
    ) -> DisputePage:
        rows, total = list_disputes(db, status=status, limit=limit, offset=offset)
        return DisputePage(
            items=[PixDisputeRead.model_validate(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    @router.get("/disputes/{dispute_id}", response_model=PixDisputeRead)
    def get_dispute(dispute_id: uuid.UUID, db: Db) -> PixDispute:
        return _get(db, PixDispute, dispute_id)

    @router.patch("/disputes/{dispute_id}", response_model=PixDisputeRead)
    def patch_dispute(
        dispute_id: uuid.UUID,
        payload: PixDisputeUpdate,
        db: Db,
    ) -> PixDispute:
        return update_dispute(db, _get(db, PixDispute, dispute_id), payload)

    @router.delete("/disputes/{dispute_id}", status_code=204)
    def delete_dispute(dispute_id: uuid.UUID, db: Db) -> None:
        db.delete(_get(db, PixDispute, dispute_id))

    return router


def _get(db: Session, model: RowModel, row_id: uuid.UUID):
    row = db.get(model, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return row


def _conflict(exc: IntegrityError) -> str:
    state = getattr(exc.orig, "sqlstate", "")
    if state == "23503":
        return "referenced row is still in use"
    if state == "23505":
        return "unique value already exists"
    return "conflict"


app = create_app()
