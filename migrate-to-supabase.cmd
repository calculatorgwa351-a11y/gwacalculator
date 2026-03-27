@echo off
setlocal
set "ROOT=%~dp0"

if exist "%ROOT%\.venv314\Scripts\python.exe" (
  set "PYTHON=%ROOT%\.venv314\Scripts\python.exe"
) else if exist "%ROOT%\.venv\Scripts\python.exe" (
  set "PYTHON=%ROOT%\.venv\Scripts\python.exe"
) else (
  set "PYTHON=python"
)

pushd "%ROOT%" >nul
"%PYTHON%" "%ROOT%scripts\migrate_sqlite_to_supabase.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul
exit /b %EXIT_CODE%
