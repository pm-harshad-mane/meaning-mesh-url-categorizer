from __future__ import annotations

import json
from dataclasses import dataclass

import boto3

from app.models import CategorizerQueueMessage


@dataclass
class QueueMessage:
    receipt_handle: str
    payload: CategorizerQueueMessage


class SqsConsumer:
    def __init__(self, queue_url: str, *, region_name: str) -> None:
        self._client = boto3.client("sqs", region_name=region_name)
        self._queue_url = queue_url

    def receive_messages(
        self,
        *,
        max_messages: int,
        wait_time_seconds: int,
        visibility_timeout: int,
    ) -> list[QueueMessage]:
        response = self._client.receive_message(
            QueueUrl=self._queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time_seconds,
            VisibilityTimeout=visibility_timeout,
        )
        messages = response.get("Messages", [])
        return [
            QueueMessage(
                receipt_handle=message["ReceiptHandle"],
                payload=CategorizerQueueMessage.model_validate(
                    json.loads(message["Body"])
                ),
            )
            for message in messages
        ]

    def delete_message(self, receipt_handle: str) -> None:
        self._client.delete_message(
            QueueUrl=self._queue_url,
            ReceiptHandle=receipt_handle,
        )
