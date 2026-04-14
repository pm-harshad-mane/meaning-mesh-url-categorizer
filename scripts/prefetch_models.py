#!/usr/bin/env python3
from __future__ import annotations

import argparse

from sentence_transformers import CrossEncoder, SentenceTransformer


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download categorizer models into a local cache directory."
    )
    parser.add_argument("--embed-model")
    parser.add_argument("--rerank-model")
    parser.add_argument("--cache-dir", required=True)
    args = parser.parse_args()

    if not args.embed_model and not args.rerank_model:
        parser.error("at least one of --embed-model or --rerank-model is required")

    if args.embed_model:
        SentenceTransformer(args.embed_model, cache_folder=args.cache_dir)

    if args.rerank_model:
        CrossEncoder(args.rerank_model, cache_folder=args.cache_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
