# Testing

## Integration suite

`backend/tests/test_integration.py` exercises the complete pipeline as real
processes talking over HTTP, using a genuine AENOR standard PDF as corpus:

1. Ingest builds an index from the PDF (24 page-documents for UNE-EN 60228)
   and prints the run summary.
2. The embedding service starts on :8001 in mock mode; /health and /embed
   are verified.
3. The backend starts with EMBED_BACKEND=remote, exactly like a worker PC,
   and with a mock LLM so no API key or network access is needed.
4. /api/chat is consumed as an SSE stream and the event order is asserted:
   sources first, then tokens, then done. This test caught a real production
   bug: the SSE library emits CRLF line endings by default, which the
   original frontend parser did not handle.
5. Source citations must reference the ingested PDF with real page labels,
   and BM25 must retrieve the chunk containing a known value from Table 1
   of the standard (7,41 ohm/km for 2,5 mm2 bare copper, page 11).
6. /api/feedback and /api/reset are verified.

Run it:

```
cd backend
python -m tests.test_integration path/to/UNE-EN_60228_2005.pdf
```

Expected output ends with `ALL 19 CHECKS PASSED`.

## Queue behavior

The queue was additionally validated with a dedicated async test during
development: the concurrency cap holds until the client finishes consuming
the stream, priorities are honored with FIFO tie-breaking, a full queue
rejects new work, and jobs whose client timed out are skipped by workers.

## What is intentionally not covered

- Real Gemini responses (require a key and billing; validated manually).
- Real Qwen3 embeddings (Qwen3-Embedding-0.6B, ~1.2 GB download; the mock
  preserves the exact code paths, only the vector values differ).
- The PyInstaller build itself, which must run on Windows;
  `packaging/build_worker.bat` includes a post-build smoke test against
  /api/health for that purpose.
