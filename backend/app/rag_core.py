"""
RAG core — hybrid retrieval (vector + BM25 + reciprocal-rank fusion) with a
condense-plus-context chat engine.

Fixes applied vs. v2.0:
  * BUG #1 (critical): removed SimilarityPostprocessor. Reciprocal-rank fusion
    replaces node scores with RRF scores (~1/(rank+60), max ~0.03), so any
    cutoff like 0.65 filtered out 100% of nodes and the LLM always received an
    empty context. Relevance filtering is now the reranker's job.
  * BUG #5/#6: retrievers (vector + BM25 + fusion) are built ONCE PER AREA and
    shared across sessions. Previously BM25 re-tokenised the whole corpus for
    every browser tab. Per-session state is now only the chat memory. Idle
    sessions are evicted after SESSION_TTL_MINUTES.
  * BUG #7: num_queries is configurable and defaults to 1 (no LLM query
    expansion). With a local model, expansion tripled latency per message.
  * BUG #8: BM25 uses a Spanish stemmer and Spanish stopwords.
  * BUG #9: use_async=False — retrieval runs inside a worker thread with no
    event loop; the async path was the historic source of "0 nodes" failures.
  * Condense and query-generation prompts are now in Spanish so intermediate
    LLM steps match the corpus language.
"""
import os
import time
import logging
import threading

import Stemmer
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core import PromptTemplate

from .config import get_settings
from .llm_backend import configure_backend, get_reranker

logger = logging.getLogger("norma.rag")

# All user-facing / corpus-facing text is Spanish (company working language).
SYSTEM_PROMPT = """
Eres el Asistente Técnico Especializado de INGECA. Extraes información precisa de la
normativa técnica proporcionada como contexto.

FORMATO DE RESPUESTA:
- Responde directamente, sin repetir la pregunta ni añadir frases de relleno.
- Sé conciso: prioriza datos concretos (valores, referencias normativas, condiciones).
- No repitas ni resumas las fuentes en el texto: la aplicación ya las muestra aparte.

CONTINUIDAD:
- Ten en cuenta el historial. Interpreta preguntas de continuación ("¿y para acero
  galvanizado?") en su contexto sin pedir que se repitan.
- Si el usuario cambia de tema, trátalo como consulta nueva sin arrastrar contexto irrelevante.

CUANDO NO HAY INFORMACIÓN SUFICIENTE:
- Si el contexto no contiene la respuesta, no inventes. Responde exactamente:
  "No he encontrado información específica sobre [tema] en la normativa actual disponible."
- Nunca menciones detalles técnicos del sistema ni archivos corruptos.

TONO: Profesional, ejecutivo, orientado a ayudar al ingeniero.
"""

# Spanish condense prompt (same placeholders as the LlamaIndex default).
CONDENSE_PROMPT = PromptTemplate(
    "Dada la siguiente conversación entre un usuario y un asistente técnico, "
    "y una pregunta de seguimiento del usuario, reformula la pregunta de "
    "seguimiento como una pregunta independiente y autocontenida, en español.\n\n"
    "Historial de la conversación:\n{chat_history}\n\n"
    "Pregunta de seguimiento: {question}\n\n"
    "Pregunta independiente:"
)

# Spanish query-generation prompt. Only used when NUM_QUERIES > 1.
QUERY_GEN_PROMPT = (
    "Eres un asistente que genera variantes de una consulta de búsqueda sobre "
    "normativa técnica industrial. Genera {num_queries} consultas de búsqueda "
    "en español, una por línea y sin numerar, relacionadas con la siguiente "
    "consulta de entrada:\n"
    "Consulta: {query}\n"
    "Consultas:\n"
)


class RAGEngine:
    """One instance per process. Indexes and retrievers are shared per area;
    chat memory is per (session, area) with TTL-based eviction."""

    def __init__(self):
        configure_backend()
        self.settings = get_settings()
        self.areas = self.settings.areas
        self._lock = threading.Lock()          # guards the dicts below
        self._indexes: dict[str, object] = {}                  # area -> index
        self._retrievers: dict[str, object] = {}               # area -> fused retriever
        self._postprocessors: list | None = None               # shared (reranker)
        # (session_id, area) -> {"engine": ChatEngine, "last_used": monotonic}
        self._sessions: dict[tuple[str, str], dict] = {}

    # ---- shared, per-area components -----------------------------------
    def _get_index(self, area: str):
        if area not in self._indexes:
            vector_dir = self.areas.get(area, {}).get("vector_dir")
            if not vector_dir or not os.path.exists(vector_dir):
                raise FileNotFoundError(f"No vector index for area '{area}' at: {vector_dir}")
            ctx = StorageContext.from_defaults(persist_dir=vector_dir)
            self._indexes[area] = load_index_from_storage(ctx)
            logger.info("Index loaded for area '%s'", area)
        return self._indexes[area]

    def _get_retriever(self, area: str):
        """Build the hybrid retriever once per area (BM25 tokenisation is
        expensive — never do it per session)."""
        if area not in self._retrievers:
            s = self.settings
            index = self._get_index(area)

            vector_retriever = index.as_retriever(similarity_top_k=s.similarity_top_k)
            bm25_retriever = BM25Retriever.from_defaults(
                nodes=list(index.docstore.docs.values()),
                similarity_top_k=s.similarity_top_k,
                stemmer=Stemmer.Stemmer("spanish"),   # BUG #8: default was English
                language="es",
            )
            self._retrievers[area] = QueryFusionRetriever(
                [vector_retriever, bm25_retriever],
                similarity_top_k=s.similarity_top_k,
                num_queries=s.num_queries,            # BUG #7: default 1 (no expansion)
                query_gen_prompt=QUERY_GEN_PROMPT,
                mode="reciprocal_rerank",
                use_async=False,                      # BUG #9: we already run in a thread
            )
            logger.info("Hybrid retriever built for area '%s'", area)
        return self._retrievers[area]

    def _get_postprocessors(self) -> list:
        # BUG #1: no SimilarityPostprocessor here — RRF scores are rank-based
        # (max ~0.03) and any absolute cutoff silently removed every node.
        # The reranker (if available) is the relevance filter now.
        if self._postprocessors is None:
            reranker = get_reranker()
            self._postprocessors = [reranker] if reranker is not None else []
        return self._postprocessors

    # ---- per-session chat engines ---------------------------------------
    def _get_engine(self, session_id: str, area: str):
        key = (session_id, area)
        with self._lock:
            entry = self._sessions.get(key)
            if entry is None:
                engine = CondensePlusContextChatEngine.from_defaults(
                    retriever=self._get_retriever(area),
                    node_postprocessors=self._get_postprocessors(),
                    memory=ChatMemoryBuffer.from_defaults(
                        token_limit=self.settings.memory_token_limit
                    ),
                    system_prompt=SYSTEM_PROMPT,
                    condense_prompt=CONDENSE_PROMPT,
                )
                entry = {"engine": engine, "last_used": time.monotonic()}
                self._sessions[key] = entry
            entry["last_used"] = time.monotonic()
            return entry["engine"]

    def reset_session(self, session_id: str) -> None:
        with self._lock:
            for key in [k for k in self._sessions if k[0] == session_id]:
                del self._sessions[key]

    def evict_idle_sessions(self) -> int:
        """Drop sessions idle for longer than SESSION_TTL_MINUTES (BUG #5:
        previously engines accumulated forever). Returns evicted count."""
        ttl = self.settings.session_ttl_minutes * 60
        now = time.monotonic()
        with self._lock:
            stale = [k for k, v in self._sessions.items() if now - v["last_used"] > ttl]
            for k in stale:
                del self._sessions[k]
        if stale:
            logger.info("Evicted %d idle session engine(s)", len(stale))
        return len(stale)

    @property
    def active_sessions(self) -> int:
        return len(self._sessions)

    # ---- the actual query ------------------------------------------------
    def stream_query(self, session_id: str, area: str, question: str):
        """Blocking. Runs inside the queue worker thread.
        Returns (token_generator, sources_list)."""
        engine = self._get_engine(session_id, area)
        response = engine.stream_chat(question)
        pdf_dir = self.areas.get(area, {}).get("pdf_dir", "")

        sources = []
        for node in getattr(response, "source_nodes", []) or []:
            meta = node.node.metadata
            fname = meta.get("file_name", "") or "Desconocido"
            sources.append({
                "archivo": fname,
                "ruta_completa": os.path.join(pdf_dir, fname) if pdf_dir and fname else "",
                "pagina": meta.get("page_label", "N/A"),
                # Reranker score if enabled, RRF score otherwise. The frontend
                # no longer displays it (RRF values are meaningless to users),
                # but it is kept for the feedback/audit trail.
                "score": round(node.score, 3) if node.score else 0.0,
            })
        return response.response_gen, sources
