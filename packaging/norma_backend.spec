# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the worker executable (norma-backend.exe).
#
# Build ON WINDOWS from the repository root:
#     packaging\build_worker.bat
#
# The exe bundles the FastAPI backend AND the local embedding stack
# (torch + sentence-transformers + transformers), because every PC embeds
# the user's question locally with Qwen3-Embedding-0.6B (self-sufficient:
# no dependency on a central service being up to answer a query). The model
# weights themselves are NOT embedded in the exe; they are downloaded to the
# HuggingFace cache on first run (or pre-seeded by the installer), so the exe
# stays a sane size and the model can be updated without rebuilding.
#
# The built Vue frontend and the .env template are installed alongside the
# exe by Inno Setup, not embedded here, so they can be updated independently.

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = (
    # uvicorn loads these dynamically
    collect_submodules("uvicorn")
    # llama-index resolves integrations dynamically
    + collect_submodules("llama_index")
    # tiktoken registers encodings through a namespace plugin
    + ["tiktoken_ext", "tiktoken_ext.openai_public"]
    # BM25 stack
    + ["Stemmer", "bm25s"]
    # Gemini client
    + collect_submodules("google.genai")
    # Local embedding stack (Qwen3-Embedding-0.6B on every PC)
    + collect_submodules("sentence_transformers")
    + collect_submodules("transformers")
    # System tray icon (pystray picks its Windows backend dynamically)
    + collect_submodules("pystray")
)

datas = (
    collect_data_files("llama_index.core")
    + collect_data_files("bm25s")
    # transformers/sentence-transformers ship data files (tokenizer helpers,
    # model card templates) that must travel with the exe.
    + collect_data_files("transformers", include_py_files=False)
    + collect_data_files("sentence_transformers", include_py_files=False)
    # The tray icon image, loaded at runtime via _MEIPASS.
    + [("launcher.ico", ".")]
)

a = Analysis(
    ["norma_backend_entry.py"],
    pathex=["../backend"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    # torch/transformers are now REQUIRED (local embedding), so they are not
    # excluded. tkinter/matplotlib/scipy/IPython remain excluded (unused).
    excludes=["tkinter", "matplotlib", "IPython"],
    noarchive=False,
)

pyz = PYZ(a.pure)

# ONEDIR mode (exclude_binaries=True + COLLECT): the exe and all its DLLs
# (torch is ~1 GB) live UNPACKED in a folder next to the exe. In the previous
# ONEFILE mode PyInstaller re-extracted that ~1 GB to a temp dir on EVERY
# launch — tens of seconds of startup plus antivirus rescans each time. ONEDIR
# extracts nothing at launch, so startup is far faster and steadier. The whole
# folder is bundled inside NormaINGECA_Setup.exe, so end users still get a
# single installer.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="norma-backend",
    icon="launcher.ico",
    console=False,         # no console window: clean UI for end users.
                           # Logs are redirected to a file by the entry point
                           # (see norma_backend_entry.py) so IT can still debug.
    upx=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="norma-backend",
)
