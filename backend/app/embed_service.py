"""
Embedding service - runs on the SINGLE ingest machine only.

Loads the embedding model once (Qwen3-Embedding-0.6B by default, same model
as the ingest run and every worker) and serves
vectors to worker PCs over the LAN. This is what allows worker installers to
ship without torch: only this machine pays the model's RAM/CPU cost.

Run on the ingest server:
    uvicorn app.embed_service:service --host 0.0.0.0 --port 8001

Endpoints:
    GET  /health -> {"status", "model", "dim"}   (workers verify model match)
    POST /embed  -> {"texts": [...], "kind": "query"|"document"}
                    returns {"vectors": [[...], ...]}

For automated tests set EMBED_SERVICE_MODEL=mock (no model download).
"""
import os
import logging

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("norma.embed_service")

# MUST match `local_embed_model` in config.py (ingest + every worker): the
# index, the ingest run and every query embedding all have to live in the
# same vector space. Only override EMBED_SERVICE_MODEL if you also change
# LOCAL_EMBED_MODEL everywhere and re-run the ingest from scratch.
MODEL_NAME = os.getenv("EMBED_SERVICE_MODEL", "Qwen/Qwen3-Embedding-0.6B")
QUERY_INSTRUCTION = os.getenv(
    "EMBED_QUERY_INSTRUCTION",
    "Represent this question for retrieving relevant technical standard passages: ",
)
MOCK_DIM = 1024

service = FastAPI(title="NormaINGECA Embedding Service")
_model = None


class EmbedRequest(BaseModel):
    texts: list[str]
    kind: str = "document"   # "query" | "document"


def _load_model():
    global _model
    if _model is not None:
        return _model
    if MODEL_NAME == "mock":
        from llama_index.core.embeddings import MockEmbedding
        _model = MockEmbedding(embed_dim=MOCK_DIM)
        logger.info("Loaded MOCK embedding model (dim=%d) - tests only", MOCK_DIM)
    else:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        _model = HuggingFaceEmbedding(
            model_name=MODEL_NAME,
            query_instruction=QUERY_INSTRUCTION,   # Qwen3 is instruction-aware
        )
        logger.info("Loaded embedding model: %s", MODEL_NAME)
    return _model


@service.on_event("startup")
def startup():
    _load_model()


@service.get("/health")
def health():
    model = _load_model()
    dim = MOCK_DIM if MODEL_NAME == "mock" else len(model.get_text_embedding("dim probe"))
    return {"status": "ok", "model": MODEL_NAME, "dim": dim}


@service.post("/embed")
def embed(req: EmbedRequest):
    model = _load_model()
    if req.kind == "query":
        vectors = [model.get_query_embedding(t) for t in req.texts]
    else:
        vectors = model.get_text_embedding_batch(req.texts)
    return {"vectors": vectors}
