@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Primero ejecuta preparar_entorno.cmd
    exit /b 1
)
".venv\Scripts\python.exe" scripts\iniciar.py %*
