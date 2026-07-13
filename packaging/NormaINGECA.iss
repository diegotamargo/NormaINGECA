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
; First run downloads the embedding model (Qwen3-Embedding-0.6B, ~1.2 GB)
; and the reranker (~1.1 GB) to the HuggingFace cache. To avoid a per-PC
; download, IT can pre-seed %USERPROFILE%\.cache\huggingface (or set HF_HOME
; to a shared read-only cache) before first launch.
; =====================================================================

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
WizardStyle=modern
PrivilegesRequired=admin
; The exe binds to 127.0.0.1 only; no firewall rule needed.

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "dist\norma-backend.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\frontend\*"; DestDir: "{app}\frontend"; Flags: ignoreversion recursesubdirs
; onlyifdoesntexist: an upgrade never overwrites a configured .env
Source: "..\backend\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist
Source: "launcher.ico"; DestDir: "{app}"

[Icons]
Name: "{autodesktop}\NormaINGECA"; Filename: "{app}\norma-backend.exe"; IconFilename: "{app}\launcher.ico"; WorkingDir: "{app}"
Name: "{group}\NormaINGECA"; Filename: "{app}\norma-backend.exe"; IconFilename: "{app}\launcher.ico"; WorkingDir: "{app}"
Name: "{group}\Editar configuracion"; Filename: "notepad.exe"; Parameters: """{app}\.env"""
Name: "{group}\Desinstalar NormaINGECA"; Filename: "{uninstallexe}"

[Run]
Filename: "notepad.exe"; Parameters: """{app}\.env"""; Description: "Revisar la configuracion (.env) ahora"; Flags: postinstall skipifsilent unchecked
Filename: "{app}\norma-backend.exe"; Description: "Iniciar NormaINGECA"; Flags: postinstall skipifsilent nowait
