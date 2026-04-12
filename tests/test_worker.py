from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.models import Category, CategorizerQueueMessage
from app.worker import Worker


class FakeStorage:
    def __init__(self) -> None:
        self.records = []
        self.deleted = []

    def put_categorization(self, record) -> None:
        self.records.append(record)

    def delete_wip(self, url_hash: str) -> None:
        self.deleted.append(url_hash)


@dataclass
class FakePipeline:
    categories: list[Category]
    fail: bool = False

    def categorize(self, title: str, content: str, *, top_k: int) -> list[Category]:
        if self.fail:
            raise RuntimeError("pipeline failed")
        return self.categories[:top_k]


def _settings() -> Settings:
    return Settings(
        aws_region="us-east-1",
        url_categorization_table="url_categorization",
        url_wip_table="url_wip",
        categorizer_queue_url="https://example.com/queue",
        taxonomy_tsv_path="taxonomy/Content_Taxonomy_3.1_2.tsv",
        embed_model_name="BAAI/bge-base-en-v1.5",
        rerank_model_name="BAAI/bge-reranker-v2-m3",
        top_k=5,
        model_version="bge-base-en-v1.5__bge-reranker-v2-m3",
        log_level="INFO",
        sqs_wait_time_seconds=10,
        sqs_visibility_timeout=300,
        ecs_poll_batch_size=10,
    )


def _message() -> CategorizerQueueMessage:
    return CategorizerQueueMessage(
        url_hash="sha256:test",
        normalized_url="https://example.com/article",
        trace_id="trace-123",
        fetched_at=100,
        http_status=200,
        content_type="text/html",
        title="Example article",
        content="Technology companies raised funding for AI tools.",
        content_fingerprint="xxh3:abc",
    )


def test_worker_writes_ready_result() -> None:
    storage = FakeStorage()
    worker = Worker(
        settings=_settings(),
        storage=storage,
        pipeline=FakePipeline(
            categories=[Category(id="IAB9", name="Technology & Computing", score=1.0, rank=1)]
        ),
    )

    worker.process_message(_message())

    assert storage.records[0].status == "ready"
    assert storage.deleted == ["sha256:test"]


def test_worker_writes_unknown_on_pipeline_failure() -> None:
    storage = FakeStorage()
    worker = Worker(
        settings=_settings(),
        storage=storage,
        pipeline=FakePipeline(categories=[], fail=True),
    )

    worker.process_message(_message())

    assert storage.records[0].status == "unknown"
    assert storage.records[0].error_code == "CATEGORIZATION_FAILED"
    assert storage.deleted == ["sha256:test"]
