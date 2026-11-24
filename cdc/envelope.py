"""JSON envelope published to SQS, one committed row per primary key.

pgoutput emits every statement. Two statements in one transaction share a
commit LSN, so a sink that dedupes on ``lsn`` + primary key would keep only
the first. The envelope is the net effect of the transaction instead:
insert then update is one insert, insert then delete is omitted, and a
delete of a row that existed before the transaction is one delete. The
``before`` image is the row as it was before the transaction, not a
mid-transaction version.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from cdc.decode import PgChange, PgTransaction
from cdc.lsn import format_lsn, lsn_sort_key, parse_lsn
from cdc.tables import APP_TABLES, AppTable

_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}")
OPS = frozenset({"insert", "update", "delete"})


@dataclass(frozen=True)
class ChangeEvent:
    op: str
    table: str
    pk: dict[str, str]
    before: dict[str, str | None] | None
    after: dict[str, str | None] | None
    lsn: str
    commit_ts: str

    def pk_json(self) -> str:
        return json.dumps(self.pk, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    def dedupe_key(self) -> tuple[str, str]:
        return (self.lsn, self.pk_json())

    def to_dict(self) -> dict[str, Any]:
        return {
            "op": self.op,
            "table": self.table,
            "pk": self.pk,
            "before": self.before,
            "after": self.after,
            "lsn": self.lsn,
            "commit_ts": self.commit_ts,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def from_json(cls, payload: str) -> ChangeEvent:
        try:
            raw = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("change event is not JSON") from exc
        if not isinstance(raw, dict):
            raise ValueError("change event must be a JSON object")
        op = raw.get("op")
        table = raw.get("table")
        if op not in OPS:
            raise ValueError(f"change event op {op!r}")
        spec = APP_TABLES.get(table)
        if spec is None:
            raise ValueError(f"change event table {table!r}")
        pk = _pk(raw.get("pk"), spec)
        before = _image(raw.get("before"), spec, field="before")
        after = _image(raw.get("after"), spec, field="after")
        if op == "insert" and after is None:
            raise ValueError("insert event has no after image")
        if op == "delete" and before is None:
            raise ValueError("delete event has no before image")
        if op == "update" and after is None:
            raise ValueError("update event has no after image")
        if op == "insert" and before is not None:
            raise ValueError("insert event has a before image")
        if op == "delete" and after is not None:
            raise ValueError("delete event has an after image")
        lsn = raw.get("lsn")
        parse_lsn(lsn)
        commit_ts = raw.get("commit_ts")
        if not isinstance(commit_ts, str):
            raise ValueError("change event commit_ts must be a string")
        partition_date(commit_ts)
        return cls(
            op=op,
            table=spec.name,
            pk=pk,
            before=before,
            after=after,
            lsn=lsn,
            commit_ts=commit_ts,
        )


def events_from_transaction(txn: PgTransaction) -> list[ChangeEvent]:
    """Net one transaction down to the rows that are visible at commit."""

    nets: dict[tuple[str, str], _Net] = {}
    order: list[tuple[str, str]] = []
    for change in txn.changes:
        spec = APP_TABLES.get(change.table)
        if spec is None or change.schema != "public":
            continue
        pk = _pk_from_change(change, spec)
        key = (spec.name, json.dumps(pk, sort_keys=True, separators=(",", ":")))
        net = nets.get(key)
        if net is None:
            net = _Net(spec.name, pk)
            nets[key] = net
            order.append(key)
        net.apply(change)
    lsn = format_lsn(txn.ack_lsn)
    commit_ts = _format_ts(txn.commit_ts)
    events: list[ChangeEvent] = []
    for key in order:
        event = nets[key].event(lsn, commit_ts)
        if event is not None:
            events.append(event)
    return events


def partition_date(commit_ts: str) -> str:
    text = commit_ts.replace("Z", "+00:00")
    try:
        moment = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid commit_ts {commit_ts!r}") from exc
    if moment.tzinfo is None:
        raise ValueError(f"commit_ts must include a timezone, got {commit_ts!r}")
    return moment.astimezone(UTC).date().isoformat()


def lsn_ord(event: ChangeEvent) -> str:
    return lsn_sort_key(event.lsn)


@dataclass
class _Net:
    table: str
    pk: dict[str, str]
    existed: bool | None = None
    present: bool = False
    before: dict[str, str | None] | None = None
    after: dict[str, str | None] | None = None

    def apply(self, change: PgChange) -> None:
        if change.op == "insert":
            if self.existed is None:
                self.existed = False
            self.after = _normalize_image(change.after)
            self.present = True
            return
        if change.op == "update":
            if self.existed is None:
                self.existed = True
                self.before = _normalize_image(change.before)
            self.after = _normalize_image(change.after)
            self.present = True
            return
        if change.op == "delete":
            if self.existed is None:
                self.existed = True
                self.before = _normalize_image(change.before)
            self.after = None
            self.present = False
            return
        raise ValueError(f"unknown change op {change.op!r}")

    def event(self, lsn: str, commit_ts: str) -> ChangeEvent | None:
        if self.existed is None:
            return None
        if not self.existed and not self.present:
            return None
        if not self.existed and self.present:
            op, before, after = "insert", None, self.after
        elif self.existed and not self.present:
            op, before, after = "delete", self.before, None
        else:
            op, before, after = "update", self.before, self.after
        return ChangeEvent(
            op=op,
            table=self.table,
            pk=dict(self.pk),
            before=before,
            after=after,
            lsn=lsn,
            commit_ts=commit_ts,
        )


def _pk_from_change(change: PgChange, spec: AppTable) -> dict[str, str]:
    image = change.after or change.before or {}
    pk: dict[str, str] = {}
    for column in spec.pk:
        value = image.get(column)
        if not isinstance(value, str) or value == "":
            raise ValueError(f"{spec.name} change is missing primary key {column}")
        pk[column] = value
    return pk


def _pk(value: object, spec: AppTable) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("change event pk must be an object")
    pk: dict[str, str] = {}
    for column in spec.pk:
        item = value.get(column)
        if not isinstance(item, str) or item == "":
            raise ValueError(f"{spec.name} event is missing primary key {column}")
        pk[column] = item
    return pk


def _image(value: object, spec: AppTable, *, field: str) -> dict[str, str | None] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"change event {field} must be an object or null")
    image: dict[str, str | None] = {}
    for column in spec.columns:
        item = value.get(column)
        if item is not None and not isinstance(item, str):
            raise ValueError(f"{spec.name}.{column} must be a string or null")
        image[column] = item
    return image


def _normalize_image(image: dict[str, str | None] | None) -> dict[str, str | None] | None:
    if image is None:
        return None
    return {key: _normalize_value(key, value) for key, value in image.items()}


def _normalize_value(column: str, value: str | None) -> str | None:
    if value is None or not column.endswith("_at"):
        return value
    return _normalize_timestamp(value)


def _normalize_timestamp(value: str) -> str:
    if not _TIMESTAMP.match(value):
        return value
    text = value.replace(" ", "T", 1)
    if text.endswith("+00"):
        text += ":00"
    if text.endswith("-00"):
        text = text[:-3] + "+00:00"
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return value
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    rendered = moment.astimezone(UTC).isoformat(timespec="microseconds")
    return rendered.replace("+00:00", "Z")


def _format_ts(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    rendered = moment.astimezone(UTC).isoformat(timespec="microseconds")
    return rendered.replace("+00:00", "Z")
