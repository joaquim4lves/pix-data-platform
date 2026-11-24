"""Append-only Parquet log of CDC events, deduped by commit LSN and primary key.

A retry of the consumer publishes the same envelope again. The object key
is new, but the row is not written when that ``lsn`` and ``pk`` are already
in the day's partition. The commit timestamp picks the partition, in UTC,
so a replay lands on the same prefix it checks.
"""

from __future__ import annotations

import io
import uuid
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from botocore.exceptions import ClientError

from cdc.aws import error_code
from cdc.envelope import ChangeEvent, lsn_ord, partition_date
from cdc.settings import CdcSettings
from cdc.tables import APP_TABLES, AppTable

MISSING = frozenset({"404", "NoSuchKey", "NoSuchBucket", "NotFound"})


def arrow_table(spec: AppTable, events: list[ChangeEvent]) -> pa.Table:
    columns: dict[str, list[str | None]] = {name: [] for name in spec.parquet_columns}
    for event in events:
        if event.table != spec.name:
            raise ValueError(f"expected {spec.name} events, got {event.table}")
        image = event.before if event.op == "delete" else event.after
        image = image or {}
        values: dict[str, str | None] = {
            "op": event.op,
            "lsn": event.lsn,
            "lsn_ord": lsn_ord(event),
            "commit_ts": event.commit_ts,
            "pk": event.pk_json(),
        }
        for name in spec.columns:
            values[name] = image.get(name)
        for name in spec.parquet_columns:
            columns[name].append(values[name])
    arrays = [pa.array(columns[name], type=pa.string()) for name in spec.parquet_columns]
    return pa.table(dict(zip(spec.parquet_columns, arrays, strict=True)))


def parquet_bytes(table: pa.Table) -> bytes:
    sink = io.BytesIO()
    pq.write_table(table, sink, compression="snappy")
    return sink.getvalue()


class CdcSink:
    def __init__(self, s3: Any, bucket: str) -> None:
        self._s3 = s3
        self._bucket = bucket

    @classmethod
    def from_settings(cls, settings: CdcSettings) -> CdcSink:
        from cdc.aws import client

        return cls(client("s3", settings), settings.bucket)

    def write(self, events: list[ChangeEvent]) -> list[str]:
        """Write unseen events. Return the object keys that were created."""

        grouped: dict[tuple[str, str], list[ChangeEvent]] = {}
        seen = self._seen_for(events)
        for event in events:
            day = partition_date(event.commit_ts)
            key = (event.table, day)
            if event.dedupe_key() in seen[key]:
                continue
            seen[key].add(event.dedupe_key())
            grouped.setdefault(key, []).append(event)
        written: list[str] = []
        for (table, day), batch in grouped.items():
            spec = APP_TABLES[table]
            body = parquet_bytes(arrow_table(spec, batch))
            first = lsn_ord(batch[0])
            object_key = f"raw/app/{table}/dt={day}/part-{first}-{uuid.uuid4().hex[:8]}.parquet"
            self._ensure_bucket()
            self._s3.put_object(
                Bucket=self._bucket,
                Key=object_key,
                Body=body,
                ContentType="application/vnd.apache.parquet",
            )
            written.append(object_key)
        return written

    def read_rows(self, table: str) -> list[dict[str, str | None]]:
        rows: list[dict[str, str | None]] = []
        for key in self._list_prefix(f"raw/app/{table}/"):
            if not key.endswith(".parquet"):
                continue
            obj = self._s3.get_object(Bucket=self._bucket, Key=key)
            loaded = pq.read_table(io.BytesIO(obj["Body"].read()))
            rows.extend(loaded.to_pylist())
        return rows

    def _seen_for(self, events: list[ChangeEvent]) -> dict[tuple[str, str], set[tuple[str, str]]]:
        needed = {(event.table, partition_date(event.commit_ts)) for event in events}
        found: dict[tuple[str, str], set[tuple[str, str]]] = {key: set() for key in needed}
        for table, day in needed:
            prefix = f"raw/app/{table}/dt={day}/"
            for key in self._list_prefix(prefix):
                if not key.endswith(".parquet"):
                    continue
                obj = self._s3.get_object(Bucket=self._bucket, Key=key)
                loaded = pq.read_table(io.BytesIO(obj["Body"].read()), columns=["lsn", "pk"])
                pairs = zip(
                    loaded.column("lsn").to_pylist(),
                    loaded.column("pk").to_pylist(),
                    strict=True,
                )
                found[(table, day)].update(pairs)
        return found

    def _list_prefix(self, prefix: str) -> list[str]:
        keys: list[str] = []
        token: str | None = None
        while True:
            kwargs: dict[str, Any] = {"Bucket": self._bucket, "Prefix": prefix}
            if token:
                kwargs["ContinuationToken"] = token
            try:
                page = self._s3.list_objects_v2(**kwargs)
            except ClientError as exc:
                if error_code(exc) in MISSING:
                    return []
                raise
            keys.extend(item["Key"] for item in page.get("Contents", []))
            if not page.get("IsTruncated"):
                return keys
            token = page.get("NextContinuationToken")

    def _ensure_bucket(self) -> None:
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
