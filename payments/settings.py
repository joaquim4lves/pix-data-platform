"""Database URL for the operational app. Defaults match docker compose."""

from __future__ import annotations

import os
from urllib.parse import quote_plus, urlsplit, urlunsplit


def database_url() -> str:
    explicit = os.environ.get("DATABASE_URL")
    if explicit:
        return explicit
    user = quote_plus(os.environ.get("POSTGRES_USER", "pix"))
    password = quote_plus(os.environ.get("POSTGRES_PASSWORD", "pix"))
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    name = quote_plus(os.environ.get("POSTGRES_DB", "pix"))
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


def libpq_url(url: str | None = None) -> str:
    text = url or database_url()
    return text.replace("postgresql+psycopg://", "postgresql://", 1).replace(
        "postgresql+psycopg2://", "postgresql://", 1
    )


def with_database(url: str, database: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, f"/{database}", parts.query, parts.fragment))
