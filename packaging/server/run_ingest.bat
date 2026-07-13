@echo off
REM Manual ingest run — double-click (or run from cmd) whenever you want to
REM refresh the indexes from the current PDFs in the shared folder.
REM Works from any Windows PC with Python 3.12, the backend requirements
REM installed, and network access to the shared folder / .env configured.
REM No scheduling: run it as often as you like, it's incremental.
cd /d "%~dp0..\..\backend"
python -m app.ingest
if errorlevel 1 (
    echo.
    echo Ingest finished with errors - check the log above.
) else (
    echo.
    echo Ingest finished OK.
)
pause
