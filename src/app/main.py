from __future__ import annotations

import logging
import time

from app.categorization.embedder import Embedder
from app.categorization.pipeline import CategorizationPipeline
from app.categorization.reranker import Reranker
from app.categorization.retriever import Retriever
from app.categorization.taxonomy_loader import load_taxonomy
from app.config import Settings
from app.logging import configure_logging
from app.queue.sqs import SqsConsumer
from app.storage.dynamodb import DynamoStorage
from app.worker import Worker

LOGGER = logging.getLogger(__name__)


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)

    consumer = SqsConsumer(settings.categorizer_queue_url, region_name=settings.aws_region)
    storage = DynamoStorage(
        settings.url_categorization_table,
        settings.url_wip_table,
        region_name=settings.aws_region,
    )
    embedder = Embedder(
        settings.embed_model_name,
        cache_dir=settings.model_cache_dir,
    )
    pipeline = CategorizationPipeline(
        retriever=Retriever(embedder),
        reranker=Reranker(
            settings.rerank_model_name,
            cache_dir=settings.model_cache_dir,
        ),
        taxonomy=load_taxonomy(settings.taxonomy_tsv_path),
    )
    worker = Worker(settings=settings, storage=storage, pipeline=pipeline)

    LOGGER.info("categorizer_started", extra={"model_version": settings.model_version})
    while True:
        messages = consumer.receive_messages(
            max_messages=settings.ecs_poll_batch_size,
            wait_time_seconds=settings.sqs_wait_time_seconds,
            visibility_timeout=settings.sqs_visibility_timeout,
        )
        if not messages:
            time.sleep(1)
            continue

        for message in messages:
            worker.process_message(message.payload)
            consumer.delete_message(message.receipt_handle)


if __name__ == "__main__":
    main()
