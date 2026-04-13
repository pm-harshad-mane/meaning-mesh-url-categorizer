from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel


class Category(BaseModel):
    id: str
    name: str
    score: float
    rank: int


class CategorizerQueueMessage(BaseModel):
    url_hash: str
    normalized_url: str
    trace_id: str
    fetched_at: int
    fetched_at_ms: int | None = None
    http_status: int
    content_type: str
    title: str
    content: str
    content_fingerprint: str


class CategorizationRecord(BaseModel):
    url_hash: str
    normalized_url: str
    status: Literal["ready", "unknown", "fetch_failed"]
    categories: list[Category]
    model_version: str
    source_http_status: int | None = None
    source_content_type: str | None = None
    title: str | None = None
    content_fingerprint: str | None = None
    first_seen_at: int
    last_updated_at: int
    expires_at: int
    trace_id: str
    error_code: str | None = None
    error_message: str | None = None
    categorizer_dequeued_at_ms: int | None = None
    categorizer_started_at_ms: int | None = None
    categorizer_finished_at_ms: int | None = None
    categorizer_queue_wait_ms: int | None = None
    categorization_compute_ms: int | None = None


@dataclass(frozen=True)
class TaxonomyEntry:
    unique_id: int
    parent_id: int | None
    tier1: str
    tier2: str
    tier3: str
    tier4: str
    path: str
    description: str


@dataclass
class RetrievalCandidate:
    unique_id: int
    parent_id: int | None
    tier1: str
    tier2: str
    tier3: str
    tier4: str
    path: str
    description: str
    faiss_score: float = 0.0
    fused_score: float = 0.0
    rerank_score: float = 0.0
