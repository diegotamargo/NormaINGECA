"""
Worker application entry point (what the packaged .exe runs).

Starts the FastAPI backend on localhost and, once the port answers, opens the
default browser at the app URL.

WHY THIS FILE IS MORE THAN "uvicorn.run(...)" (BUG #15, fixed):
Non-technical users close the browser TAB and think they closed "the
program" — but the backend process (and its console window) keeps running
in the background, still listening on APP_PORT. Next launch then hit one of
two failures, both looking like "it just doesn't open":
  1. The previous process is still genuinely alive -> the new process can't
     bind the port at all and uvicorn crashes before the browser opens.
  2. The previous process just exited (console closed) but Windows still
     holds the socket in TIME_WAIT for a short while -> an immediate
     relaunch can fail to bind even though nothing is really listening
     anymore.
Fix: before binding anything, probe /api/health. If a NormaINGECA instance
already answers, don't start a second one — just (re)open the browser tab at
it. Otherwise bind our own socket with SO_REUSEADDR so a relaunch during the
TIME_WAIT window still succeeds, and hand that socket to uvicorn.

Run from source:
    python -m app.run_app

The PyInstaller build (see packaging/) uses this module as its entry point.
"""
import logging
import socket
import sys
import threading
import time
import webbrowser

import httpx
import uvicorn

from .config import get_settings

logger = logging.getLogger("norma.run_app")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def _already_running(host: str, port: int, timeout: float = 1.0) -> bool:
    """True if a NormaINGECA instance already answers on host:port."""
    try:
        r = httpx.get(f"http://{host}:{port}/api/health", timeout=timeout)
        return r.status_code == 200 and "backend" in r.json()
    except Exception:  # noqa: BLE001 — anything other than a clean 200 means "not us"
        return False


def _open_browser_when_ready(host: str, port: int, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                webbrowser.open(f"http://{host}:{port}")
                return
        except OSError:
            time.sleep(0.3)


def _bind_socket(host: str, port: int) -> socket.socket:
    """Bind with SO_REUSEADDR so a relaunch right after closing the app does
    not fail while the old socket drains through TIME_WAIT (BUG #15)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(128)
    return sock


def main() -> None:
    s = get_settings()

    if _already_running(s.app_host, s.app_port):
        logger.info("NormaINGECA is already running on %s:%d — opening the browser "
                     "instead of starting a second instance.", s.app_host, s.app_port)
        if s.open_browser:
            webbrowser.open(f"http://{s.app_host}:{s.app_port}")
        return

    if s.open_browser:
        threading.Thread(
            target=_open_browser_when_ready,
            args=(s.app_host, s.app_port),
            daemon=True,
        ).start()

    # Import here so config/env errors surface before uvicorn starts.
    from .main import app

    try:
        sock = _bind_socket(s.app_host, s.app_port)
    except OSError:
        logger.exception(
            "Could not bind %s:%d. Something other than NormaINGECA is using "
            "this port — close it or change APP_PORT in .env.", s.app_host, s.app_port)
        sys.exit(1)

    config = uvicorn.Config(app, log_level="info")
    server = uvicorn.Server(config)
    server.run(sockets=[sock])


if __name__ == "__main__":
    main()
