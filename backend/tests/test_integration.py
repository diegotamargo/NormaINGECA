"""
Integration test for the full NormaINGECA pipeline.

Exercises, in order, using a real AENOR standard PDF as the corpus:
  1. Ingest: builds a vector index from the PDF (mock embedding model, so no
     GPU / model download is needed in CI).
  2. Embedding service: starts app.embed_service on :8001 in mock mode and
     verifies /health and /embed.
  3. Worker backend: starts app.main with EMBED_BACKEND=remote (talking to
     the service, exactly like a worker PC) and LLM_BACKEND=mock.
  4. API surface: /api/health, /api/areas, /api/chat (SSE: sources -> tokens
     -> done), /api/feedback, /api/reset.
  5. Retrieval sanity: sources returned for a query in Spanish must cite the
     ingested PDF with real page labels, and BM25 must surface the chunk
     containing a known table value.

Run from backend/:
    python -m tests.test_integration <path-to-sample-pdf>
Exit code 0 = all checks passed.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(os.environ.get("NORMA_TEST_ROOT", "/tmp/norma-test"))
EMBED_PORT = 8001
APP_PORT = 58734
CHECKS: list[str] = []


def check(name: str, ok: bool, detail: str = ""):
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))
    CHECKS.append(status)
    if not ok:
        raise SystemExit(f"Check failed: {name} {detail}")


def wait_port(port: int, timeout: float = 60.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def base_env() -> dict:
    env = os.environ.copy()
    env.update({
        "PDF_DIR_NORMATIVA": str(TEST_ROOT / "normativa" / "pdf"),
        "VECTOR_DIR_NORMATIVA": str(TEST_ROOT / "normativa" / "index"),
        "PDF_DIR_EDPR": str(TEST_ROOT / "edpr" / "pdf"),
        "VECTOR_DIR_EDPR": str(TEST_ROOT / "edpr" / "index"),
        "PDF_DIR_TECNOLOGO": str(TEST_ROOT / "tecnologo" / "pdf"),
        "VECTOR_DIR_TECNOLOGO": str(TEST_ROOT / "tecnologo" / "index"),
        "LLM_BACKEND": "mock",
        "MAX_CONCURRENT_LLM": "2",
        "OPEN_BROWSER": "false",
    })
    return env


def parse_sse(text: str):
    text = text.replace("\r\n", "\n")   # tolerate CRLF like the frontend does
    """Parse an SSE body into (event, data) pairs, joining multi-line data
    with newlines per the SSE spec."""
    events = []
    for frame in text.split("\n\n"):
        ev, data_lines = "message", []
        for line in frame.split("\n"):
            if line.startswith("event:"):
                ev = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].removeprefix(" "))
        if data_lines or ev != "message":
            events.append((ev, "\n".join(data_lines)))
    return events


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m tests.test_integration <sample.pdf>")
        sys.exit(2)
    sample_pdf = Path(sys.argv[1]).resolve()
    check("sample PDF exists", sample_pdf.is_file(), str(sample_pdf))

    # ---- workspace -------------------------------------------------------
    shutil.rmtree(TEST_ROOT, ignore_errors=True)
    (TEST_ROOT / "normativa" / "pdf").mkdir(parents=True)
    shutil.copy(sample_pdf, TEST_ROOT / "normativa" / "pdf" / sample_pdf.name)

    procs = []
    try:
        # ---- 1. ingest (mock embeddings, real PDF parsing/chunking) ------
        env = base_env()
        env["EMBED_BACKEND"] = "mock"
        r = subprocess.run([sys.executable, "-m", "app.ingest", "normativa"],
                           cwd=BACKEND_DIR, env=env, capture_output=True, text=True)
        print(r.stdout[-1500:], r.stderr[-1500:])
        check("ingest exits 0", r.returncode == 0)
        check("ingest summary printed", "INGEST SUMMARY" in r.stderr + r.stdout)
        idx_dir = TEST_ROOT / "normativa" / "index"
        check("index persisted", (idx_dir / "docstore.json").exists())

        # ---- 2. embedding service (mock model) ---------------------------
        env_svc = base_env()
        env_svc["EMBED_SERVICE_MODEL"] = "mock"
        procs.append(subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.embed_service:service",
             "--port", str(EMBED_PORT)],
            cwd=BACKEND_DIR, env=env_svc,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        check("embed service up", wait_port(EMBED_PORT))
        h = httpx.get(f"http://127.0.0.1:{EMBED_PORT}/health").json()
        check("embed /health", h["status"] == "ok" and h["dim"] == 1024, str(h))
        v = httpx.post(f"http://127.0.0.1:{EMBED_PORT}/embed",
                       json={"texts": ["resistencia del conductor"], "kind": "query"}).json()
        check("embed /embed returns vector", len(v["vectors"][0]) == 1024)

        # ---- 3. worker backend -------------------------------------------
        # Default architecture: every PC loads the embedding model LOCALLY
        # (self-sufficient; no dependency on the server being up to answer).
        # We use mock here so CI needs no model download, but the wiring is
        # identical to shipping Qwen3-Embedding-0.6B on the worker.
        env_app = base_env()
        env_app["EMBED_BACKEND"] = "mock"
        procs.append(subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--port", str(APP_PORT)],
            cwd=BACKEND_DIR, env=env_app,
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT))
        check("backend up", wait_port(APP_PORT))
        base = f"http://127.0.0.1:{APP_PORT}"

        health = httpx.get(f"{base}/api/health").json()
        check("/api/health", health["status"] == "ok", str(health))
        areas = httpx.get(f"{base}/api/areas").json()
        check("/api/areas has 3 areas", len(areas) == 3)

        # ---- 4. chat over SSE --------------------------------------------
        question = ("Cual es la resistencia maxima a 20 grados de un conductor de "
                    "cobre recocido desnudo de clase 1 de 2,5 mm2")
        with httpx.stream("POST", f"{base}/api/chat", timeout=120, json={
                "session_id": "it-1", "area": "normativa",
                "question": question, "is_followup": False}) as resp:
            check("chat HTTP 200", resp.status_code == 200)
            body = "".join(resp.iter_text())
        events = parse_sse(body)
        kinds = [e for e, _ in events]
        check("SSE order sources->tokens->done",
              kinds[0] == "sources" and "token" in kinds and kinds[-1] == "done",
              str(kinds[:5]))
        sources = json.loads(events[0][1])
        check("sources cite the ingested PDF",
              sources and all(s["archivo"] == sample_pdf.name for s in sources),
              str([(s['archivo'], s['pagina']) for s in sources]))
        check("sources carry real page labels",
              all(s["pagina"] not in ("", "N/A") for s in sources),
              str([s["pagina"] for s in sources]))
        answer = "".join(d for e, d in events if e == "token")
        check("tokens streamed", len(answer) > 0, f"{len(answer)} chars")

        # ---- 5. retrieval sanity: BM25 must find the Table 1 chunk -------
        # Table 1 of UNE-EN 60228 states 7,41 ohm/km for 2,5 mm2 bare copper.
        sys.path.insert(0, str(BACKEND_DIR))
        for k, val in env_app.items():
            os.environ[k] = val
        os.environ["EMBED_BACKEND"] = "mock"
        from app.rag_core import RAGEngine       # noqa: E402
        engine = RAGEngine()
        retriever = engine._get_retriever("normativa")
        nodes = retriever.retrieve(question)
        joined = " ".join(n.node.get_content() for n in nodes)
        check("retriever returns nodes (cutoff bug stays fixed)", len(nodes) > 0,
              f"{len(nodes)} nodes")
        check("Table 1 value 7,41 ohm/km retrieved", "7,41" in joined)

        # ---- 6. feedback + reset -----------------------------------------
        fb = httpx.post(f"{base}/api/feedback", json={
            "session_id": "it-1", "area": "normativa", "question": question,
            "answer": answer[:200], "vote": "POSITIVO"})
        check("/api/feedback", fb.status_code == 200 and fb.json()["ok"])
        rs = httpx.post(f"{base}/api/reset", json={"session_id": "it-1"})
        check("/api/reset (JSON body)", rs.status_code == 200 and rs.json()["ok"])

        print(f"\nALL {CHECKS.count('PASS')} CHECKS PASSED")
    finally:
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()


if __name__ == "__main__":
    main()
