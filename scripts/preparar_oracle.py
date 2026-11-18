"""Provision inicial mediante SQL*Plus. Nunca borra ni reutiliza usuarios existentes."""

import argparse
import getpass
import json
import os
import re
import secrets
import shutil
import string
import subprocess
import tomllib

from _comun import RAIZ, usar_entorno


def identificador(valor):
    valor = valor.upper()
    if not re.fullmatch(r'[A-Z][A-Z0-9_]{0,29}', valor):
        raise argparse.ArgumentTypeError('Usa hasta 30 caracteres: letras, numeros y guion bajo; empieza por letra.')
    return valor


def ejecutar_sqlplus(sqlplus, contenido, claves):
    resultado = subprocess.run([sqlplus, '-L', '-S', '/nolog'], input=contenido,
                               text=True, encoding='utf-8', capture_output=True, cwd=RAIZ, timeout=120,
                               env={**os.environ, 'NLS_LANG': '.AL32UTF8'})
    salida = resultado.stdout + resultado.stderr
    for clave in claves:
        if clave:
            salida = salida.replace(clave, '[oculta]')
            if len(clave) >= 8:
                salida = salida.replace(clave[:8], '[oculta]')
    salida = re.sub(r'Upc_[A-Za-z0-9_#]+', '[oculta]', salida)
    if resultado.returncode or re.search(r'\b(?:ORA|SP2|PLS)-\d+', salida):
        raise RuntimeError(f'SQL*Plus no completo la operacion (codigo {resultado.returncode}):\n' + salida)
    print(salida.strip())


def main():
    usar_entorno()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--usuario', type=identificador, default='UPC_ASISTENCIA')
    parser.add_argument('--dsn', default='localhost:1521/XEPDB1')
    parser.add_argument('--os-auth', action='store_true', help='Usar / as sysdba en el servidor local.')
    parser.add_argument('--pdb', type=identificador, default='XEPDB1')
    parser.add_argument('--admin', type=identificador, default='SYSTEM')
    parser.add_argument('--reanudar', action='store_true', help='Activar una cuenta sin autenticacion de una provision fallida.')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+:\d{1,5}/[A-Za-z0-9_.-]+', args.dsn):
        parser.error('El DSN debe tener formato host:puerto/servicio, sin contrasenas.')
    sqlplus = shutil.which('sqlplus')
    if not sqlplus:
        parser.error('SQL*Plus no esta en PATH. Instala SQL*Plus en este PC o usa el cliente del servidor Oracle.')
    destino = RAIZ / '.streamlit' / 'secrets.toml'
    pendiente = RAIZ / '.local' / 'credenciales_oracle_pendientes.toml'
    if destino.exists() or (pendiente.exists() and not args.reanudar):
        parser.error('Ya existe configuracion local o una provision pendiente. No se reemplazo; consulta la guia de recuperacion.')
    if args.reanudar and not pendiente.exists():
        parser.error('--reanudar requiere .local/credenciales_oracle_pendientes.toml de una provision anterior.')
    # Oracle XE 18c: mantener la clave generada por debajo de 30 bytes.
    clave = 'Upc_' + ''.join(secrets.choice(string.ascii_letters + string.digits + '_#') for _ in range(24))
    clave_admin = None if args.os_auth else getpass.getpass(f'Contrasena de {args.admin}: ')
    valores = {'ORACLE_USUARIO': args.usuario, 'ORACLE_CONTRASENA': clave,
               'ORACLE_DSN': args.dsn, 'APP_BASE_URL': 'https://localhost:8501'}
    if args.reanudar:
        anteriores = tomllib.loads(pendiente.read_text(encoding='utf-8'))
        if anteriores['ORACLE_USUARIO'] != args.usuario or anteriores['ORACLE_DSN'] != args.dsn:
            parser.error('El usuario y DSN deben coincidir con la provision pendiente.')
    pendiente.parent.mkdir(exist_ok=True)
    with pendiente.open('w' if args.reanudar else 'x', encoding='utf-8') as archivo:
        archivo.write('# Privado: generado por preparar_oracle.py. No compartir.\n')
        for nombre, valor in valores.items():
            archivo.write(f'{nombre} = {json.dumps(valor)}\n')
    pendiente.chmod(0o600)
    inicio = 'SET ECHO OFF\nSET VERIFY OFF\nWHENEVER OSERROR EXIT FAILURE\nWHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK\n'
    if args.os_auth:
        conexion = f'CONNECT / AS SYSDBA\nALTER SESSION SET CONTAINER = {args.pdb};\n'
    else:
        conexion = f'CONNECT {args.admin}@"//{args.dsn}"\n{clave_admin}\n'
    script_admin = 'sql/00_activar_usuario_pendiente.sql' if args.reanudar else 'sql/00_crear_usuario.sql'
    admin = inicio + conexion + f'@"{(RAIZ / script_admin).as_posix()}"\n{args.usuario}\n{clave}\n{clave}\nEXIT SUCCESS\n'
    try:
        ejecutar_sqlplus(sqlplus, admin, [clave, clave_admin])
        # Guardar la clave antes de instalar DDL para poder recuperar un fallo parcial.
        destino.parent.mkdir(exist_ok=True)
        with destino.open('x', encoding='utf-8') as archivo:
            archivo.write(pendiente.read_text(encoding='utf-8'))
        destino.chmod(0o600)
        pendiente.unlink()
        instalacion = inicio + f'CONNECT {args.usuario}@"//{args.dsn}"\n{clave}\n@"{(RAIZ / "oracle_scripts.sql").as_posix()}"\nEXIT SUCCESS\n'
        ejecutar_sqlplus(sqlplus, instalacion, [clave])
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f'{exc}\nLa clave se conserva en un archivo privado local; no repitas la creacion del usuario. Consulta docs/SQLPLUS_Y_SQLDEVELOPER.md.') from exc
    print('Esquema instalado. Credenciales locales en .streamlit/secrets.toml; no se mostraron en consola.')


if __name__ == '__main__':
    main()
