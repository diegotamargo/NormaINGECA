"""PyInstaller entry point: delegates to the worker application runner."""
import os
import sys

# When frozen, resolve relative paths (.env, frontend/) against the exe dir.
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.run_app import main  # noqa: E402

if __name__ == "__main__":
    main()
