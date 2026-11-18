"""Rutas y seleccion del interprete compartidas por los comandos del proyecto."""

import os
from pathlib import Path
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]


def usar_entorno():
    python = RAIZ / '.venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    if not python.is_file():
        raise SystemExit('Primero crea el entorno: Python 3.11 scripts/preparar_entorno.py')
    if Path(sys.prefix).resolve() != (RAIZ / '.venv').resolve():
        script = str(Path(sys.argv[0]).resolve())
        raise SystemExit(subprocess.call([str(python), script, *sys.argv[1:]], cwd=RAIZ))
    if sys.version_info[:2] != (3, 11):
        raise SystemExit('El entorno debe usar Python 3.11. Consulta docs/INSTALACION.md.')
    os.chdir(RAIZ)
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
