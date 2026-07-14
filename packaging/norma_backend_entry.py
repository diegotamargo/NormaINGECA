"""PyInstaller entry point: delegates to the worker application runner."""
import os
import sys

# When frozen, resolve relative paths (.env, frontend/) against the exe dir.
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))

    # The installer bundles the model cache into a fixed, machine-wide,
    # writable folder (ProgramData — NOT Program Files, which is read-only for
    # normal users). Point HuggingFace there so every user on the PC shares one
    # cache and the exe finds the models with ZERO per-user seeding.
    os.environ.setdefault("HF_HOME", r"C:\ProgramData\NormaINGECA\hf_cache")

    # The worker exe ships with a pre-seeded HuggingFace cache. Force OFFLINE
    # mode so sentence-transformers / huggingface_hub NEVER hit the network at
    # startup. Otherwise it fires dozens of HEAD/GET requests to huggingface.co
    # to check for file updates even when everything is cached — a few seconds
    # on a fast link, but minutes (or a hang / crash) behind a corporate proxy
    # that throttles or blocks huggingface.co.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    # The exe is built windowed (console=False) for a clean, professional UI —
    # no black console on the worker's screen. But that leaves stdout/stderr
    # with no terminal, which would swallow errors (and can even crash noisy
    # libraries writing to a null stream). Redirect both to a per-user log file
    # so end users see nothing while IT keeps a full, timestamped trace of every
    # startup, request and error to open when debugging.
    try:
        _log_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.dirname(sys.executable)),
            "NormaINGECA", "logs")
        os.makedirs(_log_dir, exist_ok=True)
        _log = open(os.path.join(_log_dir, "norma-backend.log"),
                    "a", buffering=1, encoding="utf-8")
        sys.stdout = _log
        sys.stderr = _log
    except Exception:
        pass  # never let logging setup stop the app from starting

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.run_app import main  # noqa: E402

if __name__ == "__main__":
    main()
