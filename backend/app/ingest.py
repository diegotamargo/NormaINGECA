"""
Index builder / synchroniser.

Scans each area's PDF directory and keeps its vector index up to date using
the embedding model configured in .env (local bge-m3 by default).

Improvements vs. the original v1 `ingesta.py`:
  * Uses the pluggable backend (configure_backend) instead of hard-coded Gemini.
  * `filename_as_id=True` so refresh_ref_docs tracks documents per file.
  * PDFs DELETED from the folder are now purged from the index too
    (refresh_ref_docs only adds/updates; it never removes).

Usage (from backend/):
    python -m app.ingest              # sync all areas
    python -m app.ingest normativa    # sync one area

IMPORTANT: indexes are tied to the embedding model that built them. If you
switch embedding models (e.g. Gemini -> bge-m3), delete the old index folders
and rebuild from scratch.
"""
import os
import sys
import json
import logging

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)

from .config import get_settings
from .llm_backend import configure_backend

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("norma.ingest")


def _write_suggestions(area: str, documents: list, vector_dir: str) -> None:
    """Ask the LLM for 3 short example questions grounded in this area's ACTUAL
    documents and cache them next to the index (suggestions.json). Workers read
    this file to show area-specific prompts on the empty screen. Best-effort:
    any failure (no LLM key, offline, parse error) just skips it and the UI
    falls back to generic prompts."""
    from llama_index.core import Settings
    if getattr(Settings, "llm", None) is None or not documents:
        return
    sample = "\n\n".join((getattr(d, "text", "") or "")[:1500] for d in documents[:4])
    prompt = (
        "A partir de los siguientes fragmentos de documentación técnica, "
        "redacta 3 preguntas de ejemplo, breves y concretas, que un ingeniero "
        "podría hacer sobre este contenido. Devuelve solo las 3 preguntas, una "
        "por línea, sin numerarlas ni añadir nada más.\n\n"
        f"Fragmentos:\n{sample}\n\nPreguntas:"
    )
    try:
        resp = str(Settings.llm.complete(prompt))
        questions = [ln.strip(" -•\t").strip() for ln in resp.splitlines()]
        questions = [q for q in questions if len(q) > 8][:3]
        if questions:
            with open(os.path.join(vector_dir, "suggestions.json"), "w",
                      encoding="utf-8") as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            logger.info("Wrote %d example questions for area '%s'.",
                        len(questions), area)
    except Exception:  # noqa: BLE001 — suggestions are optional, never fatal
        logger.exception("Could not generate suggestions for area '%s'", area)


def sync_area(area: str, pdf_dir: str, vector_dir: str) -> dict:
    """Sync one area's index with its PDF folder.

    Returns a stats dict:
        {"area", "status", "new", "updated", "deleted", "unchanged", "total"}
    `status` is "ok", "skipped" (unreachable folder / no PDFs) or "error".
    """
    logger.info("=== Syncing area '%s' ===", area)
    stats = {"area": area, "status": "skipped",
             "new": 0, "updated": 0, "deleted": 0, "unchanged": 0, "total": 0}

    if not pdf_dir or not os.path.exists(pdf_dir):
        logger.error("PDF directory missing or unreachable: %s — skipping", pdf_dir)
        return stats

    # An EMPTY area (folder exists but has no PDFs yet) is not an error — it is
    # simply not populated. Detect it before SimpleDirectoryReader, which would
    # otherwise raise "No files found" and mark the area as failed (making the
    # whole ingest exit non-zero over a perfectly normal empty area).
    try:
        has_pdf = any(f.lower().endswith(".pdf") for f in os.listdir(pdf_dir))
    except OSError:
        logger.error("PDF directory unreachable: %s — skipping", pdf_dir)
        return stats
    if not has_pdf:
        logger.info("No PDFs in %s yet — skipping (nothing to index).", pdf_dir)
        return stats

    try:
        documents = SimpleDirectoryReader(
            pdf_dir,
            required_exts=[".pdf"],
            filename_as_id=True,     # stable per-file ids -> refresh & purge work
        ).load_data()
    except Exception:  # noqa: BLE001 — a corrupt PDF must not abort other areas
        logger.exception("Failed to read PDFs from %s", pdf_dir)
        stats["status"] = "error"
        return stats
    if not documents:
        logger.warning("No PDFs found in %s — skipping", pdf_dir)
        return stats

    stats["total"] = len(documents)

    try:
        index_exists = vector_dir and os.path.exists(vector_dir) and os.listdir(vector_dir)
        if index_exists:
            logger.info("Existing index found. Refreshing changed/new documents...")
            ctx = StorageContext.from_defaults(persist_dir=vector_dir)
            index = load_index_from_storage(ctx)

            # Which ref docs already existed BEFORE the refresh -> tell new vs updated.
            known_before = set(index.ref_doc_info.keys())

            # refresh_ref_docs returns a bool per input doc: True = inserted/updated.
            changed_flags = index.refresh_ref_docs(documents)
            for doc, changed in zip(documents, changed_flags):
                if not changed:
                    stats["unchanged"] += 1
                elif doc.doc_id in known_before:
                    stats["updated"] += 1
                else:
                    stats["new"] += 1

            # Purge documents whose source PDF no longer exists on disk.
            current_ids = {d.doc_id for d in documents}
            stale = [rid for rid in list(index.ref_doc_info.keys()) if rid not in current_ids]
            for rid in stale:
                index.delete_ref_doc(rid, delete_from_docstore=True)
            stats["deleted"] = len(stale)
        else:
            logger.info("No index found. Building from scratch (%d documents)...", len(documents))
            index = VectorStoreIndex.from_documents(documents)
            stats["new"] = len(documents)

        os.makedirs(vector_dir, exist_ok=True)
        index.storage_context.persist(persist_dir=vector_dir)
        logger.info("Index persisted at: %s", vector_dir)
        stats["status"] = "ok"

        # (Re)generate example questions only when the corpus actually changed
        # or none exist yet — a no-op re-ingest must not spend an LLM call.
        sugg_path = os.path.join(vector_dir, "suggestions.json")
        if stats["new"] or stats["updated"] or not os.path.exists(sugg_path):
            _write_suggestions(area, documents, vector_dir)
    except Exception:  # noqa: BLE001 — one bad area must not abort the others
        logger.exception("Failed to sync area '%s'", area)
        stats["status"] = "error"

    logger.info("Area '%s': +%d new, ~%d updated, -%d deleted, =%d unchanged (%d total)",
                area, stats["new"], stats["updated"], stats["deleted"],
                stats["unchanged"], stats["total"])
    return stats


def main() -> None:
    configure_backend()
    settings = get_settings()
    only = sys.argv[1] if len(sys.argv) > 1 else None

    results = []
    for area, paths in settings.areas.items():
        if only and area != only:
            continue
        results.append(sync_area(area, paths["pdf_dir"], paths["vector_dir"]))

    # ---- Aggregated summary (handy for a quick look after a manual run) ----
    totals = {k: sum(r[k] for r in results)
              for k in ("new", "updated", "deleted", "unchanged", "total")}
    logger.info("================ INGEST SUMMARY ================")
    for r in results:
        logger.info("  %-10s [%-7s] +%d new  ~%d updated  -%d deleted  =%d unchanged  (%d total)",
                    r["area"], r["status"], r["new"], r["updated"],
                    r["deleted"], r["unchanged"], r["total"])
    logger.info("  %-10s          +%d new  ~%d updated  -%d deleted  =%d unchanged  (%d total)",
                "TOTAL", totals["new"], totals["updated"], totals["deleted"],
                totals["unchanged"], totals["total"])
    logger.info("===============================================")

    # Non-zero exit if any area failed -> run_ingest.bat prints the error
    # summary and pauses instead of closing the window.
    if any(r["status"] == "error" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
