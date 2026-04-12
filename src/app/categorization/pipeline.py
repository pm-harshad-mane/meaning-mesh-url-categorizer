from __future__ import annotations

import re

from app.categorization.reranker import Reranker
from app.categorization.retriever import Retriever
from app.models import Category, RetrievalCandidate, TaxonomyEntry

TOP_K_PER_QUERY = 10
FUSED_TOP_K = 10


class CategorizationPipeline:
    def __init__(
        self,
        *,
        retriever: Retriever,
        reranker: Reranker,
        taxonomy: list[TaxonomyEntry],
    ) -> None:
        self._retriever = retriever
        self._reranker = reranker
        self._taxonomy = taxonomy
        self._retriever.build_index(self._taxonomy)

    def categorize(self, title: str, content: str, *, top_k: int) -> list[Category]:
        queries = build_multi_queries(title=title, content=content)
        per_query_results = [
            self._retriever.search(query, top_k=TOP_K_PER_QUERY)
            for query in queries
        ]
        fused_candidates = reciprocal_rank_fusion(
            per_query_results,
            final_top_k=max(FUSED_TOP_K, top_k),
        )
        final_ranked = self._reranker.rerank(
            title=title,
            content=content,
            candidates=fused_candidates,
            top_k=top_k,
        )

        categories: list[Category] = []
        for rank, candidate in enumerate(final_ranked, start=1):
            categories.append(
                Category(
                    id=str(candidate.unique_id),
                    name=candidate.path,
                    score=round(candidate.rerank_score, 6),
                    rank=rank,
                )
            )
        return categories


def normalize_text(s: str) -> str:
    s = "" if s is None else str(s)
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def build_multi_queries(*, title: str, content: str, max_body_chars: int = 1800) -> list[str]:
    body = normalize_text(content)[:max_body_chars]

    q5: list[str] = []
    if title:
        q5.append(f"title: {normalize_text(title)}")
    if body:
        q5.append(f"content: {body}")

    queries: list[str] = []
    if q5:
        queries.append(" || ".join(q5))

    return dedupe_preserve_order([query for query in queries if normalize_text(query)])


def reciprocal_rank_fusion(
    per_query_results: list[list[RetrievalCandidate]],
    *,
    final_top_k: int,
    k: int = 60,
) -> list[RetrievalCandidate]:
    merged: dict[int, dict[str, float | RetrievalCandidate]] = {}

    for results in per_query_results:
        for rank, candidate in enumerate(results, start=1):
            if candidate.unique_id not in merged:
                merged[candidate.unique_id] = {
                    "candidate": candidate,
                    "rrf_score": 0.0,
                    "best_faiss_score": candidate.faiss_score,
                }

            merged[candidate.unique_id]["rrf_score"] = float(
                merged[candidate.unique_id]["rrf_score"]
            ) + (1.0 / (k + rank))
            merged[candidate.unique_id]["best_faiss_score"] = max(
                float(merged[candidate.unique_id]["best_faiss_score"]),
                candidate.faiss_score,
            )

    fused: list[RetrievalCandidate] = []
    for item in merged.values():
        candidate = item["candidate"]
        assert isinstance(candidate, RetrievalCandidate)
        candidate.fused_score = float(item["rrf_score"])
        candidate.faiss_score = float(item["best_faiss_score"])
        fused.append(candidate)

    fused.sort(key=lambda candidate: (candidate.fused_score, candidate.faiss_score), reverse=True)
    return fused[:final_top_k]
