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
pip install -r requirements.txt
pytest
```

Run the worker loop locally with `PYTHONPATH=src python -m app.main`.
