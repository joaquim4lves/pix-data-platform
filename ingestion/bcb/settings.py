"""Runtime configuration. Defaults target the local compose stack."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    base_url: str
    bucket: str
    region: str
    access_key_id: str
    secret_access_key: str
    endpoint_url: str | None
    lookback_months: int
    page_size: int
    timeout_seconds: float
    max_retries: int
    backoff_seconds: float

    @classmethod
    def from_env(cls) -> Settings:
        endpoint = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
        endpoint = endpoint.strip() if endpoint is not None else ""
        return cls(
            base_url=os.environ.get(
                "BCB_BASE_URL",
                "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata",
            ),
            bucket=os.environ.get("S3_BUCKET", "pix-data-local"),
            region=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
            secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
            endpoint_url=endpoint or None,
            lookback_months=_int_env("LOOKBACK_MONTHS", 3),
            page_size=_int_env("PAGE_SIZE", 50_000),
            timeout_seconds=_float_env("HTTP_TIMEOUT_SECONDS", 120.0),
            max_retries=_int_env("HTTP_MAX_RETRIES", 5),
            backoff_seconds=_float_env("HTTP_BACKOFF_SECONDS", 1.0),
        )
