"""CDC runtime configuration. Defaults match the local compose stack."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ingestion.bcb.settings import endpoint_from_env, region_from_env, static_credentials
from payments.settings import database_url


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
    session_token: str | None = None

    @classmethod
    def from_env(cls) -> CdcSettings:
        access_key_id, secret_access_key, session_token = static_credentials()
        return cls(
            database_url=database_url(),
            publication=os.environ.get("CDC_PUBLICATION", "pix_app"),
            slot=os.environ.get("CDC_SLOT", "pix_app_slot"),
            queue_name=os.environ.get("CDC_QUEUE", "pix-cdc"),
            bucket=os.environ.get("S3_BUCKET", "pix-data-local"),
            region=region_from_env(),
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            endpoint_url=endpoint_from_env(),
            session_token=session_token,
        )
