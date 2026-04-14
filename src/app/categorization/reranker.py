from __future__ import annotations

from sentence_transformers import CrossEncoder

from app.models import RetrievalCandidate


class Reranker:
    def __init__(self, model_name: str, *, cache_dir: str | None = None) -> None:
        self.model_name = model_name
        self._model = CrossEncoder(model_name, cache_folder=cache_dir)

    def build_rerank_query(
        self,
        *,
        title: str,
        content: str,
        max_chars: int = 1800,
    ) -> str:
        parts: list[str] = []
        if title:
            parts.append(f"title: {title}")
        if content:
            parts.append(f"content: {content[:max_chars]}")
        return " || ".join(parts)

    def rerank(
        self,
        *,
        title: str,
        content: str,
        candidates: list[RetrievalCandidate],
        top_k: int,
    ) -> list[RetrievalCandidate]:
        if not candidates:
            return []

        query = self.build_rerank_query(title=title, content=content)
        pairs = [(candidate.description, query) for candidate in candidates]
        scores = self._model.predict(pairs)

        ranked: list[RetrievalCandidate] = []
        for candidate, score in zip(candidates, scores):
            candidate.rerank_score = float(score)
            ranked.append(candidate)

        ranked.sort(
            key=lambda candidate: (
                candidate.rerank_score,
                candidate.fused_score,
                candidate.faiss_score,
            ),
            reverse=True,
        )
        return ranked[:top_k]
