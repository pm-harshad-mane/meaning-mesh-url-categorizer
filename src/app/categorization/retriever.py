from __future__ import annotations

from typing import Optional

import faiss

from app.categorization.embedder import Embedder
from app.models import RetrievalCandidate, TaxonomyEntry


class Retriever:
    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder
        self._taxonomy: Optional[list[TaxonomyEntry]] = None
        self._index: Optional[faiss.Index] = None

    def build_index(self, taxonomy: list[TaxonomyEntry]) -> None:
        self._taxonomy = list(taxonomy)
        docs = [entry.description for entry in self._taxonomy]
        embeddings = self._embedder.encode(docs)

        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(embeddings)

    def search(self, query_text: str, *, top_k: int) -> list[RetrievalCandidate]:
        if self._taxonomy is None or self._index is None:
            raise RuntimeError("Index not built.")

        query_vec = self._embedder.encode([query_text])
        scores, indices = self._index.search(query_vec, top_k)

        results: list[RetrievalCandidate] = []
        for score, idx in zip(scores[0], indices[0]):
            if int(idx) < 0:
                continue
            row = self._taxonomy[int(idx)]
            results.append(
                RetrievalCandidate(
                    unique_id=row.unique_id,
                    parent_id=row.parent_id,
                    tier1=row.tier1,
                    tier2=row.tier2,
                    tier3=row.tier3,
                    tier4=row.tier4,
                    path=row.path,
                    description=row.description,
                    faiss_score=float(score),
                )
            )
        return results
