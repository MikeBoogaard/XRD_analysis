@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First-time setup is needed. Follow the beginner tutorial in README.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m rsm_toolkit.gui
if errorlevel 1 pause
