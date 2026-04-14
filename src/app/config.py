from __future__ import annotations

import os
from dataclasses import dataclass


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    aws_region: str
    url_categorization_table: str
    url_wip_table: str
    categorizer_queue_url: str
    taxonomy_tsv_path: str
    model_cache_dir: str
    embed_model_name: str
    rerank_model_name: str
    top_k: int
    model_version: str
    log_level: str
    sqs_wait_time_seconds: int
    sqs_visibility_timeout: int
    ecs_poll_batch_size: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            url_categorization_table=os.getenv(
                "URL_CATEGORIZATION_TABLE",
                "url_categorization",
            ),
            url_wip_table=os.getenv("URL_WIP_TABLE", "url_wip"),
            categorizer_queue_url=os.getenv("CATEGORIZER_QUEUE_URL", ""),
            taxonomy_tsv_path=os.getenv(
                "TAXONOMY_TSV_PATH",
                "taxonomy/Content_Taxonomy_3.1_2.tsv",
            ),
            model_cache_dir=os.getenv("MODEL_CACHE_DIR", "/opt/huggingface"),
            embed_model_name=os.getenv("EMBED_MODEL_NAME", "BAAI/bge-base-en-v1.5"),
            rerank_model_name=os.getenv("RERANK_MODEL_NAME", "BAAI/bge-reranker-v2-m3"),
            top_k=_get_int("TOP_K", 5),
            model_version=os.getenv(
                "MODEL_VERSION",
                "bge-base-en-v1.5__bge-reranker-v2-m3",
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            sqs_wait_time_seconds=_get_int("SQS_WAIT_TIME_SECONDS", 10),
            sqs_visibility_timeout=_get_int("SQS_VISIBILITY_TIMEOUT", 300),
            ecs_poll_batch_size=_get_int("ECS_POLL_BATCH_SIZE", 10),
        )
