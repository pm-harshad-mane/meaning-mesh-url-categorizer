from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str, *, cache_dir: str | None = None) -> None:
        self.model_name = model_name
        self._model = SentenceTransformer(model_name, cache_folder=cache_dir)

    def encode(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")
