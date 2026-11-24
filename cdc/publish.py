"""SQS queue that sits between the replication slot and the Parquet sink."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from cdc.aws import client, error_code
from cdc.envelope import ChangeEvent
from cdc.settings import CdcSettings

_MISSING_QUEUE = frozenset({"AWS.SimpleQueueService.NonExistentQueue", "QueueDoesNotExist"})


class SqsQueue:
    def __init__(self, sqs: Any, queue_url: str) -> None:
        self._sqs = sqs
        self._url = queue_url

    @classmethod
    def from_settings(cls, settings: CdcSettings) -> SqsQueue:
        sqs = client("sqs", settings)
        url = _ensure_queue(sqs, settings.queue_name)
        return cls(sqs, url)

    def send(self, events: list[ChangeEvent]) -> None:
        if not events:
            return
        for start in range(0, len(events), 10):
            chunk = events[start : start + 10]
            entries = [
                {"Id": str(index), "MessageBody": event.to_json()}
                for index, event in enumerate(chunk)
            ]
            response = self._sqs.send_message_batch(QueueUrl=self._url, Entries=entries)
            failed = response.get("Failed") or []
            if failed:
                raise RuntimeError(f"SQS rejected {len(failed)} of {len(chunk)} change events")

    def receive(self, *, wait_seconds: int, visibility_timeout: int = 30) -> list[dict[str, str]]:
        response = self._sqs.receive_message(
            QueueUrl=self._url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=wait_seconds,
            VisibilityTimeout=visibility_timeout,
        )
        messages: list[dict[str, str]] = []
        for item in response.get("Messages", []):
            messages.append(
                {
                    "messageId": item["MessageId"],
                    "receiptHandle": item["ReceiptHandle"],
                    "body": item["Body"],
                }
            )
        return messages

    def delete(self, messages: list[dict[str, str]]) -> None:
        if not messages:
            return
        entries = [
            {"Id": item["messageId"], "ReceiptHandle": item["receiptHandle"]} for item in messages
        ]
        response = self._sqs.delete_message_batch(QueueUrl=self._url, Entries=entries)
        failed = response.get("Failed") or []
        if failed:
            raise RuntimeError(f"SQS delete failed for {len(failed)} messages")


def _ensure_queue(sqs: Any, name: str) -> str:
    try:
        return str(sqs.get_queue_url(QueueName=name)["QueueUrl"])
    except ClientError as exc:
        if error_code(exc) not in _MISSING_QUEUE:
            raise
    created = sqs.create_queue(QueueName=name)
    return str(created["QueueUrl"])
