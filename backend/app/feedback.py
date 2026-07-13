"""Feedback logging — CSV audit trail, server-side.

BUG #14: writes are serialised with a lock (multiple workers could interleave
rows) and the caller runs record() via asyncio.to_thread so the event loop is
never blocked on file I/O.
"""
import csv
import os
import datetime
import threading

FEEDBACK_FILE = os.getenv("FEEDBACK_FILE", "feedback_consultas.csv")
_HEADER = ["Timestamp", "Sesion", "Area", "Pregunta", "Respuesta", "Voto"]
_LOCK = threading.Lock()


def record(session_id: str, area: str, question: str, answer: str, vote: str) -> None:
    with _LOCK:
        is_new = not os.path.exists(FEEDBACK_FILE)
        with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if is_new:
                w.writerow(_HEADER)
            w.writerow([datetime.datetime.now().isoformat(timespec="seconds"),
                        session_id, area, question, answer, vote])
