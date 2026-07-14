"""Central configuration, loaded once from the environment / .env file."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ------------------------------------------------------------------
    # Generation LLM backend: "api" (Gemini, recommended) | "local"
    # (Ollama, needs a GPU machine) | "mock" (tests only)
    # ------------------------------------------------------------------
    llm_backend: str = "api"

    # ------------------------------------------------------------------
    # Embedding backend. MUST always match the model that built the index.
    #   "local"  - loads Qwen3-Embedding on this machine. This is the
    #              default on BOTH the ingest server and every worker PC:
    #              the query must be embedded by the same model that built
    #              the index, and the 0.6B model is light enough (~1.2 GB
    #              on disk, ~1-2 GB RAM) to ship on every machine, making
    #              each client self-sufficient (no dependency on the server
    #              being up to answer a question).
    #   "remote" - optional: ask a central embedding service over the LAN
    #              instead of loading the model locally (see embed_service).
    #   "mock"   - deterministic fake vectors (tests only)
    # Changing the LLM never requires re-indexing; changing the embedding
    # model DOES (delete the index folders and re-run ingest).
    # ------------------------------------------------------------------
    embed_backend: str = "local"
    embed_service_url: str = "http://localhost:8001"
    # Qwen3-Embedding-0.6B: strong MTEB multilingual score for its size,
    # 100+ languages, instruction-aware. Chosen over 4B/8B because embedding
    # a short question is cheap, so the quality gain of a larger model at
    # QUERY time is marginal, while its RAM/disk cost on every i3/i5 8 GB
    # worker PC is not. The reranker does the fine-grained precision pass.
    # The ingest server and all workers MUST use this same model.
    local_embed_model: str = "Qwen/Qwen3-Embedding-0.6B"
    # Prepended to queries (Qwen3 is instruction-aware; +1-5% retrieval).
    embed_query_instruction: str = "Represent this question for retrieving relevant technical standard passages: "

    # ------------------------------------------------------------------
    # API LLM (Gemini via Google AI Studio by default)
    # ------------------------------------------------------------------
    api_provider: str = "google"       # google | openai | anthropic
    api_llm_model: str = "gemini-3.1-flash-lite"
    google_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # ------------------------------------------------------------------
    # Local LLM (Ollama) - optional alternative when data must stay on-prem
    # ------------------------------------------------------------------
    ollama_base_url: str = "http://localhost:11434"
    local_llm_model: str = "qwen3:14b"
    ollama_context_window: int = 16384   # forwarded as num_ctx

    # ------------------------------------------------------------------
    # Areas -> paths (UNC paths on worker PCs, local paths on the server)
    # ------------------------------------------------------------------
    pdf_dir_normativa: str = ""
    vector_dir_normativa: str = ""
    pdf_dir_edpr: str = ""
    vector_dir_edpr: str = ""
    pdf_dir_tecnologo: str = ""
    vector_dir_tecnologo: str = ""

    # ------------------------------------------------------------------
    # Retrieval / chunking
    # ------------------------------------------------------------------
    chunk_size: int = 1024
    chunk_overlap: int = 100
    similarity_top_k: int = 4
    num_queries: int = 1        # >1 enables LLM query expansion (slower)
    # The reranker (bge-reranker-v2-m3) is the precision pass that lets a
    # small 0.6B embedder work well: it re-scores the top candidates so the
    # LLM only sees the best chunks. torch is already present for the local
    # embedder, so this adds no new dependency. Set False only on a machine
    # too memory-constrained to load it.
    use_reranker: bool = True

    # Chat memory per session (tokens) and idle-session eviction
    memory_token_limit: int = 8000
    session_ttl_minutes: int = 120

    # Auto-shutdown: exit the process after this many minutes with no chat
    # activity, so the ~2-3 GB the two models hold in RAM is freed when nobody
    # is using the app. Relaunching (tray icon / desktop shortcut) reloads them.
    # Set 0 to disable and keep the app resident.
    idle_shutdown_minutes: int = 15

    # ------------------------------------------------------------------
    # Request queue (protects the LLM from concurrent overload)
    # ------------------------------------------------------------------
    max_concurrent_llm: int = 2      # Gemini tolerates small concurrency
    max_queue_size: int = 100
    queue_timeout: int = 120         # max seconds waiting in line
    generation_timeout: int = 300    # max seconds generating one answer

    # ------------------------------------------------------------------
    # Serving
    # ------------------------------------------------------------------
    app_host: str = "127.0.0.1"
    app_port: int = 58734    # uncommon on purpose: 8000/8080/3000 collide with
                              # other local dev tools far more often. Loopback
                              # only (app_host=127.0.0.1), so Windows Firewall
                              # never prompts regardless of which port is used.
    frontend_dist_dir: str = ""      # if set, backend serves the built SPA
    open_browser: bool = False       # worker exe opens the UI on startup
    frontend_origin: str = "http://localhost:5173"   # CORS for dev only

    @property
    def areas(self) -> dict[str, dict[str, str]]:
        return {
            "normativa": {"pdf_dir": self.pdf_dir_normativa, "vector_dir": self.vector_dir_normativa},
            "edpr":      {"pdf_dir": self.pdf_dir_edpr,      "vector_dir": self.vector_dir_edpr},
            "tecnologo": {"pdf_dir": self.pdf_dir_tecnologo, "vector_dir": self.vector_dir_tecnologo},
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
