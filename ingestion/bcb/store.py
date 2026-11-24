"""S3 raw zone, quarantine prefix, and the watermark state file.

A partition write deletes every object under the month prefix and then puts
``part.parquet``. Running the same month again replaces the partition instead
of appending to it. An empty frame is refused so a missed month cannot wipe
data that is already there.
"""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime
from typing import Any

import boto3
import pyarrow as pa
import pyarrow.parquet as pq
from botocore.client import Config
from botocore.exceptions import ClientError
from pydantic import BaseModel

from ingestion.bcb.entities import EntitySpec
from ingestion.bcb.settings import Settings

STATE_KEY = "raw/bcb/_state/watermarks.json"
MISSING = frozenset({"404", "NoSuchKey", "NoSuchBucket", "NotFound"})


def partition_prefix(entity: str, ano_mes: int) -> str:
    return f"raw/bcb/{entity}/ano_mes={ano_mes}/"


def partition_key(entity: str, ano_mes: int) -> str:
    return f"{partition_prefix(entity, ano_mes)}part.parquet"


class ObjectStore:
    def __init__(self, client: Any, bucket: str) -> None:
        self._s3 = client
        self._bucket = bucket

    @classmethod
    def from_settings(cls, settings: Settings) -> ObjectStore:
        kwargs: dict[str, Any] = {
            "region_name": settings.region,
            "aws_access_key_id": settings.access_key_id,
            "aws_secret_access_key": settings.secret_access_key,
        }
        config_kwargs: dict[str, Any] = {"retries": {"max_attempts": 3, "mode": "standard"}}
        if settings.endpoint_url:
            kwargs["endpoint_url"] = settings.endpoint_url
            config_kwargs["s3"] = {"addressing_style": "path"}
        kwargs["config"] = Config(**config_kwargs)
        return cls(boto3.client("s3", **kwargs), settings.bucket)

    @property
    def bucket(self) -> str:
        return self._bucket

    def ensure_bucket(self) -> None:
        try:
            self._s3.head_bucket(Bucket=self._bucket)
            return
        except ClientError:
            pass
        region = self._s3.meta.region_name
        if region and region != "us-east-1":
            self._s3.create_bucket(
                Bucket=self._bucket,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
            return
        self._s3.create_bucket(Bucket=self._bucket)

    def load_watermarks(self) -> dict[str, int]:
        try:
            obj = self._s3.get_object(Bucket=self._bucket, Key=STATE_KEY)
        except ClientError as exc:
            if _error_code(exc) in MISSING:
                return {}
            raise
        payload = json.loads(obj["Body"].read())
        found: dict[str, int] = {}
        for name, item in payload.get("entities", {}).items():
            found[str(name)] = int(item["ano_mes"])
        return found

    def save_watermark(self, entity: str, ano_mes: int, updated_at: datetime) -> None:
        payload = self._read_state()
        entities = payload.setdefault("entities", {})
        entities[entity] = {
            "ano_mes": ano_mes,
            "updated_at": updated_at.astimezone(UTC).isoformat(timespec="seconds"),
        }
        body = json.dumps(payload, indent=2, sort_keys=True).encode()
        self._s3.put_object(
            Bucket=self._bucket,
            Key=STATE_KEY,
            Body=body,
            ContentType="application/json",
        )

    def write_partition(self, spec: EntitySpec, ano_mes: int, rows: list[BaseModel]) -> str:
        if not rows:
            raise ValueError(f"refusing to write an empty partition for {spec.name} {ano_mes}")
        table = _table(spec, rows)
        sink = io.BytesIO()
        pq.write_table(table, sink, compression="snappy")
        key = partition_key(spec.name, ano_mes)
        self._delete_prefix(partition_prefix(spec.name, ano_mes))
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=sink.getvalue(),
            ContentType="application/vnd.apache.parquet",
        )
        return key

    def put_quarantine(
        self,
        entity: str,
        ano_mes: int,
        body: bytes,
        *,
        now: datetime | None = None,
    ) -> str:
        moment = (now or datetime.now(UTC)).astimezone(UTC)
        stamp = moment.strftime("%Y%m%dT%H%M%S%fZ")
        key = f"quarantine/{entity}/ano_mes={ano_mes}/{stamp}.json"
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        return key

    def read_partition(self, entity: str, ano_mes: int) -> pa.Table:
        obj = self._s3.get_object(Bucket=self._bucket, Key=partition_key(entity, ano_mes))
        return pq.read_table(io.BytesIO(obj["Body"].read()))

    def list_keys(self, prefix: str) -> list[str]:
        keys: list[str] = []
        paginator = self._s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            keys.extend(item["Key"] for item in page.get("Contents", []))
        return sorted(keys)

    def _delete_prefix(self, prefix: str) -> None:
        keys = [{"Key": key} for key in self.list_keys(prefix)]
        for start in range(0, len(keys), 1000):
            chunk = keys[start : start + 1000]
            if chunk:
                self._s3.delete_objects(Bucket=self._bucket, Delete={"Objects": chunk})

    def _read_state(self) -> dict[str, Any]:
        try:
            obj = self._s3.get_object(Bucket=self._bucket, Key=STATE_KEY)
        except ClientError as exc:
            if _error_code(exc) in MISSING:
                return {"entities": {}}
            raise
        payload = json.loads(obj["Body"].read())
        if not isinstance(payload, dict):
            return {"entities": {}}
        payload.setdefault("entities", {})
        return payload


def _table(spec: EntitySpec, rows: list[BaseModel]) -> pa.Table:
    dumped = [row.model_dump() for row in rows]
    dumped.sort(key=lambda item: tuple(_sort_value(item[column]) for column in spec.sort_columns))
    arrays = [
        pa.array([item[field.name] for item in dumped], type=field.type) for field in spec.schema
    ]
    return pa.table(arrays, schema=spec.schema)


def _sort_value(value: object) -> tuple[bool, object]:
    """None sorts last. A raw ``None`` cannot be ordered next to an int."""

    return (value is None, value)


def _error_code(exc: ClientError) -> str:
    error = exc.response.get("Error", {})
    return str(error.get("Code", ""))
