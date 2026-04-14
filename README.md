# meaning-mesh-url-categorizer

ECS worker service for Meaning-Mesh categorization.

Responsibilities:

- poll `url_categorizer_service_queue`
- run the categorization pipeline
- write top-5 category results to `url_categorization`
- delete `url_wip` on terminal success or terminal unknown failure

This initial repo scaffold includes the required embedder/retriever/reranker pipeline shape and reads category candidates from the checked-in TSV taxonomy asset.

The categorizer now reads taxonomy entries from `taxonomy/Content_Taxonomy_3.1_2.tsv` by default.

## Local Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --index-url https://download.pytorch.org/whl/cpu torch
pip install -r requirements-dev.txt
pytest
```

Run the worker loop locally with `PYTHONPATH=src python -m app.main`.

## Build And Push Image

Build and push a Linux ARM64 image for ECS:

```bash
./scripts/build_and_push_image.sh <account-id>.dkr.ecr.us-east-1.amazonaws.com/meaning-mesh-url-categorizer:dev
```

The image build now pre-downloads the embedder and reranker models into `/opt/huggingface`
and the runtime runs in offline mode. If you change `EMBED_MODEL_NAME` or
`RERANK_MODEL_NAME`, rebuild and repush the image before deploying.

The Docker build also installs a CPU-only PyTorch wheel, which avoids pulling
the large CUDA dependency set that is unnecessary for this ECS worker.
The runtime image installs only `requirements.txt`; test-only tooling stays in
`requirements-dev.txt`.
