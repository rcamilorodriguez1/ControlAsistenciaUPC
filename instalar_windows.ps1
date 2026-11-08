# Crea el entorno virtual e instala las dependencias en Windows.
# Uso (desde la carpeta del proyecto):  powershell -ExecutionPolicy Bypass -File .\instalar_windows.ps1
#
# En Windows "webrtcvad" no trae binarios y exige Visual C++ Build Tools.
# Por eso se usa "webrtcvad-wheels" (mismo modulo, precompilado) y
# "resemblyzer" se instala sin dependencias para que no intente compilarlo.

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}

$py = ".\.venv\Scripts\python.exe"
& $py -m pip install --upgrade pip wheel
& $py -m pip install -r requirements.txt
& $py -m pip install --no-deps resemblyzer
& $py -m pip check

Write-Host "`nListo. Ejecuta la app con:  .\.venv\Scripts\streamlit.exe run principal.py"
