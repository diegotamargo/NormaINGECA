# NormaINGECA

Internal RAG (Retrieval-Augmented Generation) assistant that lets INGECA
engineers query technical standards in natural language: general norms
(AENOR / ISO), EDP specifications and technology-provider specifications.
Answers are generated in Spanish and every response cites the source PDF and
page it was retrieved from.

The user interface is in Spanish (the company working language); code,
configuration and documentation are in English.

## Architecture

The system is designed for a corporate Windows environment where 50+ workers
share a document repository on a network drive, worker laptops are modest
(i3/i5, 8 GB RAM, no GPU), and installing runtimes per PC is not acceptable.

```
Ingest (run manually, from any PC — no dedicated server yet)
  - Manual index build/refresh with Qwen3-Embedding-0.6B  (app/ingest.py)
  - Run whenever the PDF corpus changes: python -m app.ingest
  - Writes indexes to the shared folder
  - Add / update / delete / purge handled incrementally

Shared network folder (\\server\datos)
  - PDF corpora and prebuilt vector indexes, one pair per area

Worker PC (installed via Inno Setup, no Python or Node required)
  - norma-backend.exe: FastAPI backend + built Vue SPA on localhost:58734
  - Loads indexes from the shared folder
  - Query embeddings: Qwen3-Embedding-0.6B, run locally
  - Answer generation: Gemini API (gemini-3.1-flash-lite)
```

Key design decisions:

- The embedding model and the generation LLM are independent. The embedding
  model is bound to the index; the LLM only receives text and can be swapped
  through `.env` (Gemini, OpenAI, Anthropic or a local Ollama model) without
  re-indexing.
- Every PC embeds the user's question locally with Qwen3-Embedding-0.6B. A
  question must be projected into the same vector space that built the index,
  and the 0.6B model is small enough (~1.2 GB on disk, ~1-2 GB RAM) to run on
  a modest laptop. This makes each worker self-sufficient: it keeps answering
  even if the ingest server is offline. The 0.6B size is deliberate:
  embedding one short question is cheap, so a larger model would add RAM and
  disk cost on every PC for a marginal quality gain at query time. Precision
  comes from the reranker, not from a bigger embedder.
- Hybrid retrieval: dense vectors plus BM25 (Spanish stemmer and stopwords),
  fused with reciprocal-rank fusion, then re-scored by a cross-encoder
  reranker (bge-reranker-v2-m3).
- A bounded priority queue caps concurrent LLM generations end to end
  (the worker slot is held until the client finishes consuming the token
  stream), sheds load with HTTP 503 when full, and skips jobs whose client
  already timed out.
- Server-Sent Events stream sources first, then answer tokens, so the UI can
  render citations immediately.

## Repository layout

```
backend/
  app/
    main.py             FastAPI endpoints (SSE streaming) + static SPA
    rag_core.py         hybrid retrieval and per-session chat engines
    queue_manager.py    bounded priority queue for LLM calls
    llm_backend.py      pluggable LLM / embedding configuration
    embed_service.py    optional embedding HTTP service (centralized mode)
    remote_embedding.py optional embedding client (centralized mode)
    ingest.py           index build / refresh / purge, with run summary
    run_app.py          worker entry point (server + browser launch)
    config.py           all settings, loaded from .env
    schemas.py          request models
    feedback.py         thumbs up/down CSV audit trail
  tests/
    test_integration.py end-to-end pipeline test (19 checks)
  requirements.txt          full: ingest server / development
  requirements-worker.txt   minimal: what the worker exe bundles
  .env.example              shared configuration template (ingest + workers)
frontend/               Vue 3 + Vite + Pinia single-page app (Spanish UI)
packaging/
  build_worker.bat      one-command Windows build (exe + installer)
  norma_backend.spec    PyInstaller specification
  NormaINGECA.iss       Inno Setup installer script
  server/               ingest helper scripts (manual run, embed service)
docs/
  DEPLOYMENT.md         step-by-step server and worker deployment
  TESTING.md            how the test suite works and how to run it
```

## Quick start (development)

Requires Python 3.12 and Node 20.

```bash
# Backend (mock backends: no API key or model download needed)
cd backend
pip install -r requirements.txt
cp .env.example .env             # edit: set LLM_BACKEND=mock, EMBED_BACKEND=mock
uvicorn app.main:app --reload

# Frontend (dev server with /api proxy)
cd ../frontend
npm install
npm run dev                      # http://localhost:5173
```

To develop against real models, set `EMBED_BACKEND=local` (downloads
Qwen3-Embedding-0.6B on first use), `LLM_BACKEND=api` and a `GOOGLE_API_KEY`
in `.env`, and ingest a few PDFs with `python -m app.ingest`. A centralized
embedding service is also available as an option (`app/embed_service.py`
with `EMBED_BACKEND=remote`) for deployments that prefer to keep the model
off the clients.

## Production deployment

See `docs/DEPLOYMENT.md` for the complete procedure. Summary:

1. Ingest: on any PC with network access to the shared folder, install
   `requirements.txt`, configure `backend/.env.example` (folder paths; shared
   with all workers), and run `python -m app.ingest` (or double-click
   `packaging/server/run_ingest.bat`) whenever the PDF corpus changes. No
   scheduled task for now — it's a manual step.
2. Build the worker installer on any Windows machine:
   `packaging\build_worker.bat` produces
   `packaging\Output\NormaINGECA_Setup.exe`.
3. Install on worker PCs. IT edits `{app}\.env` once per machine (Gemini API
   key only; folder paths are already configured). The desktop shortcut
   starts the app and opens the browser at `http://127.0.0.1:58734`.

## Configuration

All settings live in `backend/.env`. The most relevant:

| Variable | Where | Purpose |
| --- | --- | --- |
| `LLM_BACKEND` | worker | `api` (Gemini, default), `local` (Ollama) or `mock` |
| `API_LLM_MODEL` | worker | `gemini-3.1-flash-lite` by default |
| `GOOGLE_API_KEY` | worker | Google AI Studio key; never committed |
| `EMBED_BACKEND` | both | `local` (default, every PC) or `remote` (opt-in) |
| `LOCAL_EMBED_MODEL` | both | `Qwen/Qwen3-Embedding-0.6B` (server and workers) |
| `EMBED_SERVICE_URL` | worker | only used when `EMBED_BACKEND=remote` |
| `USE_RERANKER` | both | `true`; cross-encoder precision pass |
| `PDF_DIR_* / VECTOR_DIR_*` | both | corpus and index paths (UNC on workers) |
| `MAX_CONCURRENT_LLM` | worker | concurrent generations cap |
| `FRONTEND_DIST_DIR` | worker | built SPA served by the exe |

Changing the generation LLM never requires re-indexing. Changing the
embedding model requires deleting the index folders and re-running
`python -m app.ingest` on the server.

## Testing

The integration suite ingests a real AENOR standard (UNE-EN 60228), starts
the backend as a separate process, and validates the full pipeline over
HTTP: SSE event ordering, source citations with page labels, BM25 retrieval
of a known table value (7,41 ohm/km for 2.5 mm2 bare copper from Table 1),
feedback and session reset. It also checks the optional embedding service.
Mock LLM/embedding backends make the suite runnable offline in seconds.

```bash
cd backend
python -m tests.test_integration path/to/sample.pdf
```

Corpus PDFs are proprietary (AENOR) and are never committed; `data/` is
git-ignored.

## Limitations and future work

- No authentication yet: deployments must stay inside the corporate network.
- The AI Studio free tier may use submitted content for product improvement;
  production use should run on the paid tier or a provider with a
  no-training agreement.
- First launch on each worker downloads the embedding and reranker models
  (~2.3 GB total) to the HuggingFace cache. IT can pre-seed a shared cache
  (`HF_HOME`) to avoid a per-PC download.
- Feedback is stored per machine as CSV; a shared SQLite/database sink would
  simplify analysis.
