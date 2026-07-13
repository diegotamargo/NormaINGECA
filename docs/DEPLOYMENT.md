# Deployment guide

Two roles are deployed: ingest (run manually, from any PC) and N worker PCs.
Worker PCs need nothing but the installer; ingest needs Python installed on
whichever machine runs it.

## 1. Ingest (run manually, from any PC)

There is no dedicated ingest server for now — run it manually, whenever the
PDF corpus changes, from any Windows PC with network access to the shared
folder. Requirements: Python 3.12, roughly 12 GB of free disk (model cache)
and 8 GB of RAM. A GPU is optional; the embedding model runs acceptably on
CPU.

```
cd backend
pip install -r requirements.txt
copy .env.example .env             (edit the shared folder paths; same as workers)
```

First index build (downloads Qwen3-Embedding-0.6B on first run):

```
python -m app.ingest
```

The run ends with a summary per area (new / updated / deleted / unchanged).
The script is incremental: it only embeds new or modified PDFs, and purges
index entries whose source PDF was deleted from the folder — so re-running
it after adding a handful of PDFs is cheap.

For convenience, `packaging\server\run_ingest.bat` wraps the same command
(cd + `python -m app.ingest` + pause on error) so it can be double-clicked.
No scheduling is set up at the moment: run it by hand whenever you've added
or updated PDFs in the shared folder.

Optional (centralized embedding mode only): if you prefer to keep the model
off the worker PCs, run the embedding service and set `EMBED_BACKEND=remote`
on the workers instead of the default `local`:

```
packaging\server\start_embed_service.bat
```

For unattended operation register it as a scheduled task at logon or wrap it
with a service manager such as NSSM. Verify from another machine:
`http://<server>:8001/health` must return the model name and dimension. In
the default local-embedding mode this service is not needed.

## 2. Building the worker installer

On any Windows machine with Python 3.12, Node 20 and Inno Setup 6:

```
packaging\build_worker.bat
```

The script builds the Vue frontend, produces `norma-backend.exe` with
PyInstaller (worker requirements, including the local embedding stack), runs
a smoke test against `/api/health`, and compiles
`packaging\Output\NormaINGECA_Setup.exe`.

To pre-configure all installations, edit `backend\.env.example` before
building (folder paths, which are shared across all machines). The installer
copies it as `{app}\.env` on first install and never overwrites it on
upgrades.

## 3. Worker PCs

Run `NormaINGECA_Setup.exe` (administrator). After installation, edit
`{app}\.env` once:

- `GOOGLE_API_KEY`: from https://aistudio.google.com/apikey (each PC needs
  its own key to avoid quota saturation)

Folder paths (`PDF_DIR_*`, `VECTOR_DIR_*`) are already configured in the
`.env` and shared with all workers and ingest runs — no need to edit them
unless your company's shared folder structure changes.

The desktop shortcut starts the application; it opens the default browser at
`http://127.0.0.1:58734`. Closing the console window stops it. If you close
just the browser tab and reopen the app later, it detects the still-running
instance and reopens the browser at it instead of failing to start a second
one; if the process had actually exited, it rebinds cleanly even if Windows
is still draining the old socket. No firewall rule is ever needed — the app
binds to 127.0.0.1 only, and Windows Firewall doesn't filter loopback
traffic regardless of which port is used.

On first launch the worker downloads the embedding model
(Qwen3-Embedding-0.6B) and the reranker (bge-reranker-v2-m3), about 2.3 GB
total, to the HuggingFace cache under `%USERPROFILE%\.cache\huggingface`.
To avoid a per-PC download, pre-seed that folder or point `HF_HOME` at a
shared read-only cache before first launch.

Resource footprint per worker: roughly 400-600 MB of RAM at rest, short CPU
spikes during retrieval, no model downloads. Answer latency is dominated by
the Gemini API call (typically one to three seconds).

## 4. Updating

- Documents: drop PDFs into the shared folder, then run `run_ingest.bat`
  (or `python -m app.ingest`) manually from any PC with access to the
  folder. Updated PDFs replace their old vectors; deleted PDFs are purged.
- Application: rebuild the installer and re-run it on the workers (the
  configured `.env` is preserved).
- Configuration (`.env`): the same `.env.example` template is used by ingest
  and all workers. Folder paths are pre-configured and shared; only
  `GOOGLE_API_KEY` differs per worker. When updating shared settings
  (e.g. folder structure), edit `backend\.env.example` before rebuilding the
  installer, so all new installations pick up the change automatically.
- Generation model: edit `API_LLM_MODEL` in `.env.example` (or on individual
  machines). No re-indexing.
- Embedding model: it must stay `Qwen/Qwen3-Embedding-0.6B` everywhere
  (ingest and every worker) — they all have to embed into the same vector
  space. If you ever change it, update `LOCAL_EMBED_MODEL` on every machine,
  delete the index folders, and re-run the ingest from scratch.

## Security notes

- The worker backend binds to 127.0.0.1 only.
- API keys live in each machine's `.env`, which is git-ignored and never
  overwritten by upgrades. Do not embed keys in the installer if it will be
  distributed outside IT.
- The embedding service is unauthenticated by design and must only be
  reachable inside the corporate network.
