"""
FastAPI application — the server the Vue front end talks to.

Endpoints:
  GET  /api/health      -> liveness + queue depth + active sessions
  GET  /api/areas       -> list of document areas
  POST /api/chat        -> Server-Sent Events stream (sources, tokens, done)
  POST /api/feedback    -> record thumbs up/down
  POST /api/reset       -> clear a session's conversation memory

Fixes applied vs. v2.0:
  * BUG #10: overload now returns a real HTTP 503 before the SSE stream opens
    (previously the README promised 503 but the code sent SSE-error over 200).
  * BUG #2: the queue slot is released in a `finally` only after the token
    stream is fully consumed (or the client disconnects), so the concurrency
    cap covers generation, not just retrieval.
  * BUG #13: /api/reset takes a JSON body (it was a query parameter).
  * BUG #14: feedback writes go through asyncio.to_thread + a lock instead of
    blocking the event loop.
  * BUG #5: a background janitor evicts idle session engines periodically.

All machine-facing text is English; every string a worker can see is Spanish.
"""
import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .config import get_settings
from .schemas import ChatRequest, FeedbackRequest, ResetRequest
from .rag_core import RAGEngine
from .queue_manager import LLMQueue, QueueFullError, compute_priority
from . import feedback

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("norma.api")

# User-facing messages (Spanish — company working language).
MSG_OVERLOADED = "El sistema está saturado en este momento. Inténtalo de nuevo en unos segundos."
MSG_TIMEOUT = "La consulta ha superado el tiempo de espera. Inténtalo de nuevo."
MSG_INTERNAL = "Ha ocurrido un error interno procesando la consulta."

engine: RAGEngine | None = None
queue: LLMQueue | None = None
_janitor: asyncio.Task | None = None


async def _session_janitor():
    """Evict idle per-session chat engines every 5 minutes (BUG #5)."""
    while True:
        await asyncio.sleep(300)
        try:
            engine.evict_idle_sessions()
        except Exception:  # noqa: BLE001 — janitor must never die
            logger.exception("session janitor failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, queue, _janitor
    logger.info("Starting NormaINGECA v2 backend...")
    engine = RAGEngine()          # configures backend; indexes load lazily
    queue = LLMQueue()
    await queue.start()
    _janitor = asyncio.create_task(_session_janitor())
    yield
    _janitor.cancel()
    await queue.stop()


app = FastAPI(title="NormaINGECA v2 API", lifespan=lifespan)

_settings = get_settings()

# CORS is only relevant when the browser calls the backend on a DIFFERENT
# origin than the page — i.e. during frontend development (Vite on :5173).
# In production the built SPA is served by the StaticFiles mount below, so the
# browser talks to the same origin and CORS never applies. We allow the
# configured origin plus the usual Vite dev origins (including the :5174
# fallback Vite picks when :5173 is busy, and the 127.0.0.1 spelling).
_dev_origins = {
    _settings.frontend_origin,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
}
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(o for o in _dev_origins if o),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "backend": _settings.llm_backend,
        "queue_depth": queue.depth if queue else None,
        "active_sessions": engine.active_sessions if engine else None,
    }


@app.get("/api/areas")
async def areas():
    labels = {"normativa": "Normativa General (AENOR/ISO)",
              "edpr": "Especificaciones EDP",
              "tecnologo": "Especificaciones Tecnólogo"}
    return [{"key": k, "label": labels.get(k, k)} for k in _settings.areas]


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if req.area not in _settings.areas:
        raise HTTPException(400, f"Unknown area: {req.area}")

    # BUG #10: shed load with a real 503 before opening the SSE stream.
    if queue.is_full:
        raise HTTPException(503, MSG_OVERLOADED)

    async def event_stream():
        release = None
        try:
            # 1) Retrieval + generation setup run inside the queue worker.
            priority = compute_priority(req.is_followup, req.question)
            try:
                (gen, sources), release = await queue.submit(
                    lambda: engine.stream_query(req.session_id, req.area, req.question),
                    priority=priority,
                )
            except QueueFullError:          # queue filled between check and put
                yield {"event": "error", "data": MSG_OVERLOADED}
                return
            except (asyncio.TimeoutError, TimeoutError):
                yield {"event": "error", "data": MSG_TIMEOUT}
                return
            except Exception:  # noqa: BLE001
                logger.exception("chat failed for area=%s", req.area)
                yield {"event": "error", "data": MSG_INTERNAL}
                return

            # 2) Sources first so the UI can render the panel immediately.
            yield {"event": "sources", "data": json.dumps(sources, ensure_ascii=False)}

            # 3) Stream tokens. The generator is blocking -> pull in a thread.
            def _next(it):
                try:
                    return next(it)
                except StopIteration:
                    return None

            try:
                while True:
                    token = await asyncio.to_thread(_next, gen)
                    if token is None:
                        break
                    yield {"event": "token", "data": token}
            except Exception:  # noqa: BLE001 — LLM failure mid-stream must not
                # crash the SSE generator silently; report it like any other error.
                logger.exception("generation failed mid-stream for area=%s", req.area)
                yield {"event": "error", "data": MSG_INTERNAL}
                return

            yield {"event": "done", "data": ""}
        finally:
            # BUG #2: free the worker slot ONLY once streaming is over —
            # also runs when the client disconnects mid-stream.
            if release is not None:
                release()

    # sep="\n": some SSE client parsers split frames on "\n\n"; the library
    # default "\r\n" would silently break them (caught by the integration test).
    return EventSourceResponse(event_stream(), sep="\n")


@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    # BUG #14: file I/O off the event loop; feedback.record() is lock-guarded.
    await asyncio.to_thread(feedback.record, req.session_id, req.area,
                            req.question, req.answer, req.vote)
    return {"ok": True}


@app.post("/api/reset")
async def reset(req: ResetRequest):     # BUG #13: JSON body, not query param
    engine.reset_session(req.session_id)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Static frontend (worker deployment): if FRONTEND_DIST_DIR points to the
# built Vue SPA, the backend serves it directly at "/" so worker PCs run a
# single process on localhost with no Node.js installed. Mounted last so it
# never shadows the /api routes above.
# ---------------------------------------------------------------------------
if _settings.frontend_dist_dir and os.path.isdir(_settings.frontend_dist_dir):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=_settings.frontend_dist_dir, html=True),
              name="frontend")
    logger.info("Serving frontend from %s", _settings.frontend_dist_dir)
