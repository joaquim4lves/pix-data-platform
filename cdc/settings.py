"""CDC runtime configuration. Defaults match the local compose stack."""

from __future__ import annotations

import os
from dataclasses import dataclass

from payments.settings import database_url


def _aws_endpoint() -> str | None:
    endpoint = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
    endpoint = endpoint.strip() if endpoint is not None else ""
    return endpoint or None


@dataclass(frozen=True)
class CdcSettings:
    database_url: str
    publication: str
    slot: str
    queue_name: str
    bucket: str
    region: str
    access_key_id: str
    secret_access_key: str
    endpoint_url: str | None

    @classmethod
    def from_env(cls) -> CdcSettings:
        return cls(
            database_url=database_url(),
            publication=os.environ.get("CDC_PUBLICATION", "pix_app"),
            slot=os.environ.get("CDC_SLOT", "pix_app_slot"),
            queue_name=os.environ.get("CDC_QUEUE", "pix-cdc"),
            bucket=os.environ.get("S3_BUCKET", "pix-data-local"),
            region=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
            secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
            endpoint_url=_aws_endpoint(),
        )
