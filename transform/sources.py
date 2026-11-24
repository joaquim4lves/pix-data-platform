"""Where a build reads raw Parquet from.

Model SQL never calls ``read_parquet``. The runner registers a view per
entity under ``raw``, either from a local directory that mirrors the
ingestion layout or from ``s3://`` through the httpfs extension. LocalStack
is the development endpoint: path-style HTTP, same as the ingestion client.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from ingestion.bcb.settings import Settings


@dataclass(frozen=True)
class LocalRaw:
    root: Path


@dataclass(frozen=True)
class S3Raw:
    bucket: str
    prefix: str
    region: str
    access_key_id: str
    secret_access_key: str
    endpoint_url: str | None


RawLocation = LocalRaw | S3Raw


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def parquet_glob(location: RawLocation, entity: str) -> str:
    """Partition glob for ``raw/bcb/<entity>/ano_mes=YYYYMM/part.parquet``."""

    if isinstance(location, LocalRaw):
        return str(location.root / "bcb" / entity / "ano_mes=*" / "part.parquet")
    prefix = location.prefix.strip("/")
    return f"s3://{location.bucket}/{prefix}/bcb/{entity}/ano_mes=*/part.parquet"


def s3_statements(location: S3Raw) -> list[str]:
    """DuckDB settings that let httpfs read this bucket.

    A set endpoint (LocalStack, or any other S3-compatible URL) uses path-style
    addressing. An empty endpoint leaves DuckDB on its default virtual-hosted
    client, which is what real AWS uses in v0.4.
    """

    statements = ["INSTALL httpfs", "LOAD httpfs"]
    if location.endpoint_url:
        parsed = urlparse(location.endpoint_url)
        host = parsed.netloc or parsed.path
        if not host:
            raise ValueError(f"AWS endpoint URL has no host: {location.endpoint_url}")
        use_ssl = "false" if parsed.scheme == "http" else "true"
        statements.append(f"SET s3_endpoint={sql_literal(host)}")
        statements.append(f"SET s3_use_ssl={use_ssl}")
        statements.append("SET s3_url_style='path'")
    statements.append(f"SET s3_region={sql_literal(location.region)}")
    statements.append(f"SET s3_access_key_id={sql_literal(location.access_key_id)}")
    statements.append(f"SET s3_secret_access_key={sql_literal(location.secret_access_key)}")
    return statements


def location_from_env() -> RawLocation:
    kind = os.environ.get("PIX_RAW_SOURCE", "local").strip().lower()
    if kind == "local":
        return LocalRaw(Path(os.environ.get("PIX_RAW_ROOT", "data/raw")))
    if kind == "s3":
        settings = Settings.from_env()
        return S3Raw(
            bucket=settings.bucket,
            prefix=os.environ.get("PIX_RAW_PREFIX", "raw"),
            region=settings.region,
            access_key_id=settings.access_key_id,
            secret_access_key=settings.secret_access_key,
            endpoint_url=settings.endpoint_url,
        )
    raise ValueError(f"PIX_RAW_SOURCE must be 'local' or 's3', got {kind!r}")
