from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Protocol

from app.config import Settings
from app.models import CategorizationRecord, CategorizerQueueMessage, Category
from app.utils.time import unix_timestamp_ms

LOGGER = logging.getLogger(__name__)


class StorageProtocol(Protocol):
    def put_categorization(self, record: CategorizationRecord) -> None: ...

    def delete_wip(self, url_hash: str) -> None: ...


class PipelineProtocol(Protocol):
    def categorize(self, title: str, content: str, *, top_k: int) -> list[Category]: ...


@dataclass
class Worker:
    settings: Settings
    storage: StorageProtocol
    pipeline: PipelineProtocol
    now_ms: Callable[[], int] = unix_timestamp_ms

    def process_message(self, message: CategorizerQueueMessage) -> None:
        dequeued_at_ms = self.now_ms()
        started_at_ms = self.now_ms()
        fetch_completed_at_ms = message.fetched_at_ms or (message.fetched_at * 1000)
        queue_wait_ms = max(0, dequeued_at_ms - fetch_completed_at_ms)

        try:
            categories = self.pipeline.categorize(
                message.title,
                message.content,
                top_k=self.settings.top_k,
            )
            finished_at_ms = self.now_ms()
            finished_at = finished_at_ms // 1000
            compute_ms = max(0, finished_at_ms - started_at_ms)
            record = CategorizationRecord(
                url_hash=message.url_hash,
                normalized_url=message.normalized_url,
                status="ready",
                categories=categories,
                model_version=self.settings.model_version,
                source_http_status=message.http_status,
                source_content_type=message.content_type,
                title=message.title,
                content_fingerprint=message.content_fingerprint,
                first_seen_at=finished_at,
                last_updated_at=finished_at,
                expires_at=finished_at + 2_592_000,
                trace_id=message.trace_id,
                categorizer_dequeued_at_ms=dequeued_at_ms,
                categorizer_started_at_ms=started_at_ms,
                categorizer_finished_at_ms=finished_at_ms,
                categorizer_queue_wait_ms=queue_wait_ms,
                categorization_compute_ms=compute_ms,
            )
            LOGGER.info(
                "categorization_completed",
                extra={
                    "url_hash": message.url_hash,
                    "trace_id": message.trace_id,
                    "categorizer_queue_wait_ms": queue_wait_ms,
                    "categorization_compute_ms": compute_ms,
                },
            )
        except Exception as exc:
            finished_at_ms = self.now_ms()
            finished_at = finished_at_ms // 1000
            compute_ms = max(0, finished_at_ms - started_at_ms)
            LOGGER.exception(
                "categorization_failed",
                extra={
                    "url_hash": message.url_hash,
                    "trace_id": message.trace_id,
                    "categorizer_queue_wait_ms": queue_wait_ms,
                    "categorization_compute_ms": compute_ms,
                },
            )
            record = CategorizationRecord(
                url_hash=message.url_hash,
                normalized_url=message.normalized_url,
                status="unknown",
                categories=[
                    Category(id="UNKNOWN", name="Unknown", score=1.0, rank=1)
                ],
                model_version=self.settings.model_version,
                source_http_status=message.http_status,
                source_content_type=message.content_type,
                title=message.title,
                content_fingerprint=message.content_fingerprint,
                first_seen_at=finished_at,
                last_updated_at=finished_at,
                expires_at=finished_at + 2_592_000,
                trace_id=message.trace_id,
                error_code="CATEGORIZATION_FAILED",
                error_message=str(exc),
                categorizer_dequeued_at_ms=dequeued_at_ms,
                categorizer_started_at_ms=started_at_ms,
                categorizer_finished_at_ms=finished_at_ms,
                categorizer_queue_wait_ms=queue_wait_ms,
                categorization_compute_ms=compute_ms,
            )

        self.storage.put_categorization(record)
        self.storage.delete_wip(message.url_hash)
