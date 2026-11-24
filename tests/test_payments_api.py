"""Operational API. CRUD runs when Postgres is reachable; OpenAPI does not need it."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import psycopg
import pytest
from fastapi.testclient import TestClient
from payments.api import create_app, get_db
from payments.cli import migrate
from payments.settings import database_url, libpq_url, with_database
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


@pytest.fixture(scope="module")
def payments_database() -> str:
    admin = database_url()
    try:
        with psycopg.connect(libpq_url(admin), autocommit=True, connect_timeout=2) as conn:
            conn.execute("select 1")
            found = conn.execute("select 1 from pg_database where datname = 'pix_test'").fetchone()
            if found is None:
                conn.execute("create database pix_test")
    except Exception as exc:
        pytest.skip(f"Postgres is not available: {exc}")
    url = with_database(admin, "pix_test")
    migrate(url)
    return url


@pytest.fixture
def client(payments_database: str):
    engine = create_app(payments_database).state.engine
    with engine.begin() as conn:
        conn.execute(text("truncate pix_disputes, pix_transactions, pix_keys"))
    app = create_app(payments_database)
    with TestClient(app) as test_client:
        yield test_client
    app.state.engine.dispose()
    engine.dispose()


def test_openapi_lists_the_operational_routes() -> None:
    paths = create_app().openapi()["paths"]
    for path in ("/health", "/keys", "/keys/{key_id}", "/transactions", "/disputes"):
        assert path in paths


def test_health_is_503_when_the_database_fails() -> None:
    app = create_app()

    def broken() -> object:
        class Bad:
            def execute(self, *_args: object, **_kwargs: object) -> None:
                raise OperationalError("select 1", {}, Exception("down"))

            def commit(self) -> None:
                return None

            def rollback(self) -> None:
                return None

            def close(self) -> None:
                return None

        yield Bad()

    app.dependency_overrides[get_db] = broken
    response = TestClient(app).get("/health")
    assert response.status_code == 503


def test_migration_sets_replica_identity_full(payments_database: str) -> None:
    migrate(payments_database)
    with psycopg.connect(libpq_url(payments_database)) as conn:
        rows = conn.execute(
            """
            select c.relname, c.relreplident
            from pg_class c
            join pg_namespace n on n.oid = c.relnamespace
            where n.nspname = 'public'
              and c.relname in ('pix_keys', 'pix_transactions', 'pix_disputes')
            """
        ).fetchall()
    assert {name: ident for name, ident in rows} == {
        "pix_keys": "f",
        "pix_transactions": "f",
        "pix_disputes": "f",
    }


def test_key_transaction_and_dispute_crud(client: TestClient) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    created = client.post("/keys", json=_key())
    assert created.status_code == 201
    body = created.json()
    key_id = body["id"]
    assert body["ispb"] == "05938780"
    assert body["municipio_ibge"] == 3550308

    duplicate = client.post("/keys", json=_key())
    assert duplicate.status_code == 409
    assert "unique" in duplicate.json()["detail"]

    invalid = client.post("/keys", json=_key(ispb="123"))
    assert invalid.status_code == 422

    patched = client.patch(f"/keys/{key_id}", json={"status": "inactive"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "inactive"
    listed = client.get("/keys", params={"status": "inactive", "ispb": "05938780"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    missing = client.get(f"/keys/{uuid.uuid4()}")
    assert missing.status_code == 404

    occurred = datetime(2026, 11, 24, 15, tzinfo=UTC).isoformat()
    payment = client.post(
        "/transactions",
        json={
            "end_to_end_id": "E0593878020261124150000000000001",
            "amount": "12.34",
            "payer_ispb": "05938780",
            "receiver_ispb": "00000000",
            "municipio_ibge": 3550308,
            "forma_iniciacao": "DICT",
            "direction": "outbound",
            "status": "settled",
            "occurred_at": occurred,
        },
    )
    assert payment.status_code == 201
    payment_id = payment.json()["id"]
    assert payment.json()["amount"] == "12.34"

    dispute = client.post(
        "/disputes",
        json={
            "transaction_id": payment_id,
            "reason": "scam",
            "opened_at": occurred,
        },
    )
    assert dispute.status_code == 201
    dispute_id = dispute.json()["id"]

    blocked = client.delete(f"/transactions/{payment_id}")
    assert blocked.status_code == 409
    assert "referenced" in blocked.json()["detail"]

    assert client.delete(f"/disputes/{dispute_id}").status_code == 204
    assert client.delete(f"/transactions/{payment_id}").status_code == 204
    assert client.delete(f"/keys/{key_id}").status_code == 204
    assert client.get("/keys").json()["total"] == 0


def _key(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "key_type": "Aleatória",
        "key_value": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "person_type": "PF",
        "ispb": "05938780",
        "municipio_ibge": 3550308,
        "status": "active",
    }
    body.update(overrides)
    return body
