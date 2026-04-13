# Categorizer Contracts

Input queue message:

```json
{
  "url_hash": "sha256:...",
  "normalized_url": "https://example.com/page",
  "trace_id": "trace-...",
  "fetched_at": 1775862008,
  "fetched_at_ms": 1775862008123,
  "http_status": 200,
  "content_type": "text/html",
  "title": "Page title",
  "content": "Extracted text content",
  "content_fingerprint": "xxh3:..."
}
```

Output DynamoDB result:

- writes `status = "ready"` with top-5 categories on success
- writes `status = "unknown"` with the Unknown category on terminal failure
- persists categorizer timing fields:
  - `categorizer_dequeued_at_ms`
  - `categorizer_started_at_ms`
  - `categorizer_finished_at_ms`
  - `categorizer_queue_wait_ms`
  - `categorization_compute_ms`
- deletes the matching `url_wip` item for terminal outcomes
- loads category candidates from the checked-in TSV taxonomy asset
