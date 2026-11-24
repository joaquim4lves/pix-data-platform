"""Parquet sink dedupe and partial SQS batches. No Docker."""

from __future__ import annotations

import pytest
from cdc.apply import apply_queue
from cdc.envelope import ChangeEvent
from cdc.handler import handler
from cdc.publish import SqsQueue
from cdc.settings import CdcSettings
from cdc.sink import CdcSink
from moto import mock_aws


def _event(lsn: str, row_id: str, status: str, commit_ts: str) -> ChangeEvent:
    image = {
        "id": row_id,
        "key_type": "CPF",
        "key_value": row_id,
        "person_type": "PF",
        "ispb": "05938780",
        "municipio_ibge": "3550308",
        "status": status,
        "created_at": "2026-11-24T12:00:00.000000Z",
        "updated_at": commit_ts,
    }
    return ChangeEvent(
        op="insert",
        table="pix_keys",
        pk={"id": row_id},
        before=None,
        after=image,
        lsn=lsn,
        commit_ts=commit_ts,
    )


@pytest.fixture
def aws(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ENDPOINT_URL", "")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("S3_BUCKET", "pix-test")
    monkeypatch.setenv("CDC_QUEUE", "pix-cdc-test")
    with mock_aws():
        yield CdcSettings.from_env()


def test_repeat_of_the_same_lsn_and_pk_does_not_add_a_row(aws: CdcSettings) -> None:
    sink = CdcSink.from_settings(aws)
    event = _event("0/10", "key-1", "active", "2026-11-24T15:00:00.000000Z")
    later = _event("0/20", "key-1", "inactive", "2026-11-25T01:00:00.000000Z")
    first = sink.write([event, event])
    second = sink.write([event, later])
    rows = sink.read_rows("pix_keys")
    assert len(first) == 1
    assert len(second) == 1
    assert sorted((row["lsn"], row["status"]) for row in rows) == [
        ("0/10", "active"),
        ("0/20", "inactive"),
    ]
    assert {key.split("/")[3] for key in first + second} == {"dt=2026-11-24", "dt=2026-11-25"}


def test_handler_reports_only_the_bad_record(aws: CdcSettings) -> None:
    good = _event("0/10", "key-1", "active", "2026-11-24T15:00:00.000000Z")
    result = handler(
        {
            "Records": [
                {"messageId": "ok", "body": good.to_json()},
                {"messageId": "bad", "body": "{"},
            ]
        },
        None,
    )
    assert result == {"batchItemFailures": [{"itemIdentifier": "bad"}]}
    assert CdcSink.from_settings(aws).read_rows("pix_keys")[0]["id"] == "key-1"
    again = ChangeEvent.from_json(good.to_json())
    assert again.dedupe_key() == good.dedupe_key()


def test_apply_deletes_successes_and_counts_a_poison_message(aws: CdcSettings) -> None:
    queue = SqsQueue.from_settings(aws)
    queue.send([_event("0/10", "key-1", "active", "2026-11-24T15:00:00.000000Z")])
    queue._sqs.send_message(QueueUrl=queue._url, MessageBody="{")
    result = apply_queue(aws, wait_seconds=0)
    assert result.deleted == 1
    assert result.failed == 1
    assert len(CdcSink.from_settings(aws).read_rows("pix_keys")) == 1
