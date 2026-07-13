"""
Pluggable LLM + embedding backend.

Design principle: the generation LLM and the embedding model are INDEPENDENT.
  * The embedding model is bound to the index (it built the vectors). By
    default (EMBED_BACKEND=local) it runs locally wherever it's needed: on
    whichever PC runs the ingest, and on every worker PC for query
    embeddings. A centralized alternative (embed_service.py, consumed via
    remote_embedding.py) exists as an opt-in for deployments that prefer to
    keep the model off the clients, but it is not the default. Changing the
    embedding model requires re-indexing.
  * The generation LLM only ever sees text (retrieved chunks + question), so
    it can be swapped freely via .env: Gemini today, Ollama or another API
    tomorrow, no re-indexing.

Backends:
  LLM_BACKEND   = api (Gemini/OpenAI/Anthropic) | local (Ollama) | mock (tests)
  EMBED_BACKEND = remote (worker PCs) | local (ingest server) | mock (tests)
"""
import logging

from llama_index.core import Settings

from .config import get_settings

logger = logging.getLogger("norma.llm")


def configure_backend() -> None:
    """Wire llama_index global Settings to the selected backends."""
    s = get_settings()
    Settings.chunk_size = s.chunk_size
    Settings.chunk_overlap = s.chunk_overlap

    if s.llm_backend == "api":
        _configure_api_llm(s)
    elif s.llm_backend == "local":
        _configure_local_llm(s)
    elif s.llm_backend == "mock":
        from llama_index.core.llms import MockLLM
        Settings.llm = MockLLM(max_tokens=64)
    else:
        raise ValueError(f"Unknown LLM_BACKEND: {s.llm_backend!r}")

    _configure_embeddings(s)
    logger.info("Backends configured: llm=%s embed=%s", s.llm_backend, s.embed_backend)


# ---------------------------------------------------------------------------
# Generation LLM
# ---------------------------------------------------------------------------
def _configure_api_llm(s) -> None:
    """Cloud API for generation. Verify the provider's data-use terms before
    sending internal documents (AI Studio free tier may use data for
    improvement; the paid tier does not)."""
    provider = s.api_provider
    if provider == "google":
        from llama_index.llms.google_genai import GoogleGenAI
        Settings.llm = GoogleGenAI(model=s.api_llm_model, api_key=s.google_api_key)
    elif provider == "openai":
        from llama_index.llms.openai import OpenAI
        Settings.llm = OpenAI(model=s.api_llm_model, api_key=s.openai_api_key)
    elif provider == "anthropic":
        from llama_index.llms.anthropic import Anthropic
        Settings.llm = Anthropic(model=s.api_llm_model, api_key=s.anthropic_api_key)
    else:
        raise ValueError(f"Unknown API_PROVIDER: {provider!r}")


def _configure_local_llm(s) -> None:
    """Ollama on a GPU machine. context_window is forwarded as num_ctx so the
    prompt (system + memory + chunks) is never silently truncated; thinking is
    disabled so qwen3 does not stream chain-of-thought to users."""
    from llama_index.llms.ollama import Ollama
    Settings.llm = Ollama(
        model=s.local_llm_model,
        base_url=s.ollama_base_url,
        request_timeout=float(s.generation_timeout),
        context_window=s.ollama_context_window,
        thinking=False,
        keep_alive="30m",
    )


# ---------------------------------------------------------------------------
# Embeddings (must match the index)
# ---------------------------------------------------------------------------
def _configure_embeddings(s) -> None:
    if s.embed_backend == "remote":
        from .remote_embedding import RemoteEmbedding, check_service
        info = check_service(s.embed_service_url)   # fail fast + log model
        logger.info("Embedding service: %s (model=%s, dim=%s)",
                    s.embed_service_url, info.get("model"), info.get("dim"))
        Settings.embed_model = RemoteEmbedding(service_url=s.embed_service_url,
                                               model_name=str(info.get("model")))
    elif s.embed_backend == "local":
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=s.local_embed_model,
            query_instruction=s.embed_query_instruction,
        )
    elif s.embed_backend == "mock":
        from llama_index.core.embeddings import MockEmbedding
        Settings.embed_model = MockEmbedding(embed_dim=1024)
    else:
        raise ValueError(f"Unknown EMBED_BACKEND: {s.embed_backend!r}")


# ---------------------------------------------------------------------------
# Optional reranker (needs torch -> off by default; only for deployments
# where the backend runs on the same machine as the models)
# ---------------------------------------------------------------------------
def get_reranker():
    s = get_settings()
    if not s.use_reranker:
        return None
    try:
        from llama_index.core.postprocessor import SentenceTransformerRerank
        return SentenceTransformerRerank(model="BAAI/bge-reranker-v2-m3",
                                         top_n=s.similarity_top_k)
    except Exception as e:  # optional; degrade gracefully
        logger.warning("Reranker unavailable, continuing without it: %s", e)
        return None
