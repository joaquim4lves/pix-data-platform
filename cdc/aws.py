"""boto3 clients pointed at LocalStack or at real AWS.

A non-empty endpoint uses path-style S3, the same switch as the ingestion
writer. An empty endpoint leaves the default virtual-hosted client.
"""

from __future__ import annotations

from typing import Any

import boto3
from botocore.client import Config

from cdc.settings import CdcSettings


def client(service: str, settings: CdcSettings) -> Any:
    kwargs: dict[str, Any] = {"region_name": settings.region}
    if settings.access_key_id:
        kwargs["aws_access_key_id"] = settings.access_key_id
    if settings.secret_access_key:
        kwargs["aws_secret_access_key"] = settings.secret_access_key
    if settings.session_token:
        kwargs["aws_session_token"] = settings.session_token
    if settings.endpoint_url:
        kwargs["endpoint_url"] = settings.endpoint_url
        if service == "s3":
            kwargs["config"] = Config(s3={"addressing_style": "path"})
    return boto3.client(service, **kwargs)


def error_code(exc: BaseException) -> str:
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        return str(response.get("Error", {}).get("Code", ""))
    return ""
