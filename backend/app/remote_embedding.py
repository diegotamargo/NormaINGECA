"""
Remote embedding client.

Worker PCs do not load the embedding model (that would require torch and
several GB of RAM on every machine). Instead, the ingest server exposes a
small HTTP service (see embed_service.py) and workers request the embedding
of the user's question over the LAN. Payloads are tiny (one short sentence
per query), so latency is negligible compared to LLM generation.

The service and the index MUST use the same embedding model; the backend
verifies this at startup via the service's /health endpoint.
"""
from typing import Any, List

import httpx
from llama_index.core.embeddings import BaseEmbedding


class RemoteEmbedding(BaseEmbedding):
    """llama-index embedding that delegates to the ingest server's service."""

    service_url: str = "http://localhost:8001"
    timeout: float = 30.0

    def __init__(self, service_url: str, model_name: str = "remote", **kwargs: Any):
        super().__init__(model_name=model_name, **kwargs)
        self.service_url = service_url.rstrip("/")

    # ---- internals -----------------------------------------------------
    def _post(self, texts: List[str], kind: str) -> List[List[float]]:
        resp = httpx.post(
            f"{self.service_url}/embed",
            json={"texts": texts, "kind": kind},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["vectors"]

    # ---- sync API (llama-index calls these) ----------------------------
    def _get_query_embedding(self, query: str) -> List[float]:
        return self._post([query], "query")[0]

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._post([text], "document")[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._post(texts, "document")

    # ---- async API ------------------------------------------------------
    async def _aget_query_embedding(self, query: str) -> List[float]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.service_url}/embed",
                                     json={"texts": [query], "kind": "query"})
            resp.raise_for_status()
            return resp.json()["vectors"][0]

    async def _aget_text_embedding(self, text: str) -> List[float]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.service_url}/embed",
                                     json={"texts": [text], "kind": "document"})
            resp.raise_for_status()
            return resp.json()["vectors"][0]


def check_service(service_url: str) -> dict:
    """Return the service's /health payload (raises on connection failure).
    Used at backend startup to fail fast with a clear message instead of
    returning empty retrievals later."""
    resp = httpx.get(f"{service_url.rstrip('/')}/health", timeout=10.0)
    resp.raise_for_status()
    return resp.json()
