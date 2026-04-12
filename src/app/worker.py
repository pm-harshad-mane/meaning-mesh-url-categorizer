from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from app.config import Settings
from app.models import CategorizationRecord, CategorizerQueueMessage, Category
from app.utils.time import unix_timestamp

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

    def process_message(self, message: CategorizerQueueMessage) -> None:
        now = unix_timestamp()
        try:
            categories = self.pipeline.categorize(
                message.title,
                message.content,
                top_k=self.settings.top_k,
            )
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
                first_seen_at=now,
                last_updated_at=now,
                expires_at=now + 2_592_000,
                trace_id=message.trace_id,
            )
        except Exception as exc:
            LOGGER.exception(
                "categorization_failed",
                extra={"url_hash": message.url_hash, "trace_id": message.trace_id},
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
                first_seen_at=now,
                last_updated_at=now,
                expires_at=now + 2_592_000,
                trace_id=message.trace_id,
                error_code="CATEGORIZATION_FAILED",
                error_message=str(exc),
            )

        self.storage.put_categorization(record)
        self.storage.delete_wip(message.url_hash)
