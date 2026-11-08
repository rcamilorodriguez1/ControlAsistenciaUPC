# Crea el entorno virtual e instala las dependencias en Windows.
# Uso (desde la carpeta del proyecto):
#     powershell -ExecutionPolicy Bypass -File .\instalar_windows.ps1
#
# En Windows "webrtcvad" no trae binarios y exige Visual C++ Build Tools.
# Por eso se usa "webrtcvad-wheels" (mismo modulo, precompilado) y
# "resemblyzer" se instala sin dependencias para que no intente compilarlo.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Fallar($mensaje) {
    Write-Host "`nERROR: $mensaje" -ForegroundColor Red
    exit 1
}

# 1. Buscar un Python compatible (3.11 a 3.13). 3.14 aun no tiene dlib/torch.
$python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($v in "3.11", "3.12", "3.13") {
        & py "-$v" -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) { $python = @("py", "-$v"); break }
    }
}
if (-not $python -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $ver = & python -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
    if ($ver -in "3.11", "3.12", "3.13") { $python = @("python") }
}
if (-not $python) {
    Fallar "No se encontro Python 3.11-3.13. Instala Python 3.11 desde https://www.python.org/downloads/ (marca 'Add python.exe to PATH') y vuelve a ejecutar."
}
Write-Host "Usando: $($python -join ' ')" -ForegroundColor Cyan

# 2. Crear el entorno virtual
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creando entorno virtual .venv ..."
    $argsPython = @($python | Select-Object -Skip 1) + @("-m", "venv", ".venv")
    & $python[0] @argsPython
    if ($LASTEXITCODE -ne 0) { Fallar "No se pudo crear el entorno virtual." }
}

# 3. Instalar dependencias (requiere internet; descarga ~1 GB la primera vez)
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install --upgrade pip wheel
& $py -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Fallar "Fallo la instalacion de requirements.txt" }
& $py -m pip install --no-deps resemblyzer==0.1.4
if ($LASTEXITCODE -ne 0) { Fallar "Fallo la instalacion de resemblyzer" }

# 4. Comprobar que todo importa
& $py -c "import streamlit, dlib, face_recognition_models, oracledb, torch, librosa, webrtcvad; from resemblyzer import VoiceEncoder; print('Dependencias OK')"
if ($LASTEXITCODE -ne 0) { Fallar "Alguna dependencia no se pudo importar." }

Write-Host "`nListo. Ejecuta la app con:" -ForegroundColor Green
Write-Host "    .\.venv\Scripts\streamlit.exe run principal.py"
