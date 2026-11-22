@echo off
rem Ejecuta el overlay desde el codigo fuente (sin compilar).
cd /d "%~dp0.."
if not exist .venv\Scripts\pythonw.exe (
    python -m venv .venv && .venv\Scripts\python -m pip install -r requirements.txt
)
start "" .venv\Scripts\pythonw.exe src\main.py
