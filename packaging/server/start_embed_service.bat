@echo off
REM Runs the embedding service on the ingest machine (keep it running:
REM worker PCs request query embeddings from it on port 8001).
REM First run downloads Qwen3-Embedding-0.6B (~1.2 GB) to the HuggingFace
REM cache. Must match LOCAL_EMBED_MODEL used everywhere else (ingest and
REM every worker) - they all share the same vector space.
cd /d "%~dp0..\..\backend"
python -m uvicorn app.embed_service:service --host 0.0.0.0 --port 8001
pause
