"""Arranca Streamlit con el venv del proyecto y HTTPS de desarrollo por defecto."""

import argparse
import os
import subprocess
import sys
from urllib.parse import urlsplit, urlunsplit

from _comun import RAIZ, usar_entorno


def main():
    usar_entorno()
    from src.configuracion import obtener_configuracion
    from src.utilidades.enlaces import crear_enlace_union
    from preparar_https import preparar_certificados

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', help='URL que recibira el QR, p. ej. https://192.168.1.20:8501')
    parser.add_argument('--escuchar', default='127.0.0.1', help='Para LAN: 0.0.0.0')
    parser.add_argument('--puerto', type=int, default=8501)
    parser.add_argument('--http', action='store_true', help='HTTP explicito, solo para desarrollo o un proxy TLS.')
    args = parser.parse_args()
    if not 1 <= args.puerto <= 65535:
        parser.error('El puerto debe estar entre 1 y 65535.')
    url = args.url or obtener_configuracion('APP_BASE_URL', 'https://localhost:8501')
    if args.http and not args.url:
        partes = urlsplit(url)
        url = urlunsplit(('http', partes.netloc, partes.path, '', ''))
    try:
        crear_enlace_union('verificacion', url)
    except ValueError as exc:
        parser.error(str(exc))
    partes = urlsplit(url)
    if partes.scheme != ('http' if args.http else 'https'):
        parser.error('La URL debe coincidir con el protocolo servido. Usa https:// o --http de forma explicita.')
    if partes.path not in ('', '/'):
        parser.error('Este arranque local sirve en la raiz: la URL no debe incluir subrutas.')
    if (partes.port or (443 if partes.scheme == 'https' else 80)) != args.puerto:
        parser.error('El puerto de --url debe coincidir con --puerto.')
    os.environ['APP_BASE_URL'] = url.rstrip('/')
    comando = [sys.executable, '-m', 'streamlit', 'run', str(RAIZ / 'principal.py'),
               '--server.address', args.escuchar, '--server.port', str(args.puerto),
               '--browser.serverAddress', partes.hostname, '--browser.serverPort', str(args.puerto)]
    if not args.http:
        cert, clave, _ = preparar_certificados([partes.hostname])
        comando += ['--server.sslCertFile', str(cert), '--server.sslKeyFile', str(clave)]
    print('Aplicacion y QR:', os.environ['APP_BASE_URL'], flush=True)
    print('HTTPS local requiere confiar en .certs/ca.pem; consulta docs/INSTALACION.md.', flush=True)
    try:
        raise SystemExit(subprocess.call(comando, cwd=RAIZ))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
