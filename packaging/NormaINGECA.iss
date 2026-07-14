; =====================================================================
; NormaINGECA v2 - worker PC installer
; Build after packaging\build_worker.bat has produced packaging\dist:
;     iscc NormaINGECA.iss
; Output: packaging\Output\NormaINGECA_Setup.exe
;
; What it installs (no Python, no Node required on the worker):
;   {app}\norma-backend.exe    single-process backend + web UI, with the
;                              local embedding stack bundled in
;   {app}\frontend\            built Vue SPA (served by the exe)
;   {app}\.env                 shared configuration (from .env.example;
;                              IT fills GOOGLE_API_KEY; folder paths are
;                              pre-baked and shared with all workers + ingest)
;
; Configuration (.env) is shared across ingest and workers — same folder
; paths, same embedding model. Each worker needs its own GOOGLE_API_KEY
; to avoid quota saturation.
;
; The embedding model (Qwen3-Embedding-0.6B) and the reranker
; (bge-reranker-v2-m3) are BUNDLED in this installer (~2.3 GB) and installed
; to C:\ProgramData\NormaINGECA\hf_cache. The exe points HF_HOME there and runs
; fully OFFLINE, so a worker downloads nothing and never touches huggingface.co.
; No manual cache seeding on any PC.
; =====================================================================

; Read the builder's HuggingFace hub cache at COMPILE time (iscc runs on the
; build machine). Both models must already live here (normalised under hub\).
#define HFHubCache GetEnv("USERPROFILE") + "\.cache\huggingface\hub"

[Setup]
AppName=NormaINGECA
AppVersion=2.0.0
AppPublisher=INGECA
DefaultDirName={autopf}\NormaINGECA
DefaultGroupName=NormaINGECA
OutputBaseFilename=NormaINGECA_Setup
SetupIconFile=launcher.ico
UninstallDisplayIcon={app}\norma-backend.exe
Compression=lzma2
SolidCompression=yes
; The bundled models push the payload past the ~4.2 GB limit for a single
; Setup.exe. Disk spanning splits it into Setup.exe + Setup-1.bin, Setup-2.bin…
; The install experience is unchanged (double-click Setup.exe); just distribute
; the whole Output folder together. ~2 GB slices keep the file count low.
DiskSpanning=yes
DiskSliceSize=2100000000
WizardStyle=modern
PrivilegesRequired=admin
; The exe binds to 127.0.0.1 only; no firewall rule needed.

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
; ONEDIR build: dist\norma-backend\ holds norma-backend.exe + its _internal\
; folder (all DLLs). Copy the whole folder into {app}, so {app}\norma-backend.exe
; sits next to {app}\_internal\.
Source: "dist\norma-backend\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "..\frontend\dist\*"; DestDir: "{app}\frontend"; Flags: ignoreversion recursesubdirs
; Bundled model cache -> machine-wide, writable ProgramData folder. The exe's
; HF_HOME points here (C:\ProgramData\NormaINGECA\hf_cache), so HuggingFace
; resolves both models under hf_cache\hub with no download and no per-user seed.
; nocompression: model weights (.safetensors) are near-incompressible random
; data. Compressing them with lzma2 wastes many minutes for almost no size
; saving. Store them as-is so the build takes minutes, not tens of minutes.
Source: "{#HFHubCache}\models--Qwen--Qwen3-Embedding-0.6B\*"; DestDir: "{commonappdata}\NormaINGECA\hf_cache\hub\models--Qwen--Qwen3-Embedding-0.6B"; Flags: ignoreversion recursesubdirs nocompression
Source: "{#HFHubCache}\models--BAAI--bge-reranker-v2-m3\*"; DestDir: "{commonappdata}\NormaINGECA\hf_cache\hub\models--BAAI--bge-reranker-v2-m3"; Flags: ignoreversion recursesubdirs nocompression
; onlyifdoesntexist: an upgrade never overwrites a configured .env
; .env.dist holds the real shared paths + key (git-ignored). .env.example
; stays blank as the public GitHub template.
Source: "..\backend\.env.dist"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist
Source: "launcher.ico"; DestDir: "{app}"

[Icons]
Name: "{autodesktop}\NormaINGECA"; Filename: "{app}\norma-backend.exe"; IconFilename: "{app}\launcher.ico"; WorkingDir: "{app}"
Name: "{group}\NormaINGECA"; Filename: "{app}\norma-backend.exe"; IconFilename: "{app}\launcher.ico"; WorkingDir: "{app}"
Name: "{group}\Editar configuracion"; Filename: "notepad.exe"; Parameters: """{app}\.env"""
Name: "{group}\Desinstalar NormaINGECA"; Filename: "{uninstallexe}"

[Run]
Filename: "notepad.exe"; Parameters: """{app}\.env"""; Description: "Revisar la configuracion (.env) ahora"; Flags: postinstall skipifsilent unchecked
Filename: "{app}\norma-backend.exe"; Description: "Iniciar NormaINGECA"; Flags: postinstall skipifsilent nowait
