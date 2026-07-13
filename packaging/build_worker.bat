@echo off
REM =====================================================================
REM Builds the worker deliverables on a Windows machine:
REM   1. Vue frontend      -> frontend\dist
REM   2. norma-backend.exe -> packaging\dist\norma-backend.exe
REM   3. Installer         -> packaging\Output\NormaINGECA_Setup.exe
REM Prerequisites: Python 3.12, Node 20+, Inno Setup 6 (iscc on PATH).
REM Run from the repository root:  packaging\build_worker.bat
REM =====================================================================
setlocal
cd /d "%~dp0.."

echo [1/4] Building frontend...
cd frontend
call npm install || goto :error
call npm run build || goto :error
cd ..

echo [2/4] Installing worker Python dependencies...
python -m pip install --upgrade pip pyinstaller || goto :error
python -m pip install -r backend\requirements-worker.txt || goto :error

echo [3/4] Building norma-backend.exe...
cd packaging
python -m PyInstaller --clean --noconfirm norma_backend.spec || goto :error

echo [4/4] Smoke test: starting the exe and probing /api/health...
REM Use mock backends for the smoke test so the build needs no API key
REM and no model download; this only verifies the exe boots and serves.
(
  echo LLM_BACKEND=mock
  echo EMBED_BACKEND=mock
  echo APP_HOST=127.0.0.1
  echo APP_PORT=58734
  echo FRONTEND_DIST_DIR=frontend
  echo OPEN_BROWSER=false
) > dist\.env
mkdir dist\frontend 2>nul
xcopy /e /y /q ..\frontend\dist dist\frontend\ >nul
start "" /min dist\norma-backend.exe
timeout /t 8 /nobreak >nul
curl -s http://127.0.0.1:58734/api/health || echo SMOKE TEST FAILED - inspect dist\norma-backend.exe manually
taskkill /im norma-backend.exe /f >nul 2>&1
REM Remove the smoke-test .env so the installer ships the real template.
del /q dist\.env >nul 2>&1

echo Building installer with Inno Setup...
iscc NormaINGECA.iss || goto :error

echo.
echo Done. Installer at: packaging\Output\NormaINGECA_Setup.exe
exit /b 0

:error
echo BUILD FAILED (step above). Aborting.
exit /b 1
