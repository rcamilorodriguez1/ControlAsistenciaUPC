"""Crea el venv local con Python 3.11; no copia ni reemplaza entornos existentes."""

import argparse
import platform
from pathlib import Path
import subprocess
import sys
import venv

RAIZ = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sin-instalar', action='store_true', help='Solo comprobar/crear el venv.')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 11) or platform.architecture()[0] != '64bit':
        parser.error('Usa Python 3.11 de 64 bits: py -3.11 scripts/preparar_entorno.py (Windows).')
    entorno = RAIZ / '.venv'
    python = entorno / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    if not entorno.exists():
        venv.EnvBuilder(with_pip=True).create(entorno)
    if not python.is_file():
        parser.error('El .venv existente esta incompleto o pertenece a otro sistema. Renombralo y vuelve a ejecutar.')
    version = subprocess.check_output([str(python), '-c', 'import sys; print("%d.%d" % sys.version_info[:2])'], text=True).strip()
    if version != '3.11':
        parser.error('El .venv existente no usa Python 3.11. Conserva ese entorno aparte y crea uno nuevo.')
    if not args.sin_instalar:
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(RAIZ / 'requirements.txt')], cwd=RAIZ, check=True)
        subprocess.run([str(python), '-m', 'pip', 'check'], cwd=RAIZ, check=True)
    print('Entorno listo:', python)
    print('Siguiente paso: ejecutar scripts/preparar_oracle.py con ese Python.')


if __name__ == '__main__':
    main()
