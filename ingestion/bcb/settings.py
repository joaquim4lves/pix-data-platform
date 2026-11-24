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


# Lambda rejects an empty environment value, so ``aws`` is the deployed
# spelling of "real AWS". An empty string remains the local spelling.
_REAL_AWS_ENDPOINTS = frozenset({"", "aws", "none", "off"})


def endpoint_from_env() -> str | None:
    """S3 endpoint, or None when the client should use real AWS.

    The variable is unset on a laptop that has not copied ``.env``: that
    still means LocalStack, which is the v0.1 default. A blank value, or
    the sentinels ``aws``, ``none``, and ``off``, mean the default AWS
    endpoint and virtual-hosted S3. See ADR-004.
    """

    if "AWS_ENDPOINT_URL" not in os.environ:
        return "http://localhost:4566"
    raw = os.environ.get("AWS_ENDPOINT_URL") or ""
    endpoint = raw.strip()
    if endpoint.lower() in _REAL_AWS_ENDPOINTS:
        return None
    return endpoint


def region_from_env() -> str:
    """Region for the SDK. Lambda sets ``AWS_REGION`` and forbids overriding it."""

    return os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"


def static_credentials() -> tuple[str, str, str | None]:
    """Explicit keys, or empty strings when boto3 should use its own chain.

    LocalStack has no role to assume, so a custom endpoint with no keys
    falls back to the compose dummy pair. Real AWS (Lambda, SSO, a profile)
    leaves the keys empty unless the process exported them. A session token
    is required for the temporary credentials Lambda injects.
    """

    access = os.environ.get("AWS_ACCESS_KEY_ID", "")
    secret = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    if endpoint_from_env() is not None:
        access = access or "test"
        secret = secret or "test"
    token = (os.environ.get("AWS_SESSION_TOKEN") or "").strip() or None
    return access, secret, token


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
    session_token: str | None = None

    @classmethod
    def from_env(cls) -> Settings:
        access_key_id, secret_access_key, session_token = static_credentials()
        return cls(
            base_url=os.environ.get(
                "BCB_BASE_URL",
                "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata",
            ),
            bucket=os.environ.get("S3_BUCKET", "pix-data-local"),
            region=region_from_env(),
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            endpoint_url=endpoint_from_env(),
            lookback_months=_int_env("LOOKBACK_MONTHS", 3),
            page_size=_int_env("PAGE_SIZE", 50_000),
            timeout_seconds=_float_env("HTTP_TIMEOUT_SECONDS", 120.0),
            max_retries=_int_env("HTTP_MAX_RETRIES", 5),
            backoff_seconds=_float_env("HTTP_BACKOFF_SECONDS", 1.0),
            session_token=session_token,
        )
