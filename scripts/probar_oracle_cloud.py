"""Comprueba Oracle Cloud por TLS sin cambiar la configuración de Oracle local."""
import argparse
from getpass import getpass
import json
from pathlib import Path
import re
import socket
import sys

import oracledb

from _comun import RAIZ, usar_entorno


def leer_parametros(archivo):
    try:
        dsn = Path(archivo).read_text(encoding='utf-8-sig').strip()
    except (OSError, UnicodeError):
        raise ValueError('No se pudo leer el archivo privado de conexión cloud.') from None
    if not dsn or '\\' in dsn:
        raise ValueError('Revisa la cadena cloud: no debe estar vacía ni contener barras invertidas.')
    try:
        parametros = oracledb.ConnectParams()
        parametros.parse_connect_string(dsn)
        protocolos = parametros.protocol
        if not isinstance(protocolos, list):
            protocolos = [protocolos]
        hosts = parametros.host
        if not isinstance(hosts, list):
            hosts = [hosts]
        if (not protocolos or any(p != 'tcps' for p in protocolos)
                or not parametros.ssl_server_dn_match or not parametros.service_name
                or not hosts or any(not isinstance(h, str) or not h.endswith('.oraclecloud.com') for h in hosts)):
            raise ValueError
        # Evitar los reintentos prolongados del descriptor durante esta comprobación.
        parametros.set(retry_count=0, retry_delay=0, tcp_connect_timeout=10,
                       ssl_server_dn_match=True)
    except (oracledb.Error, ValueError, TypeError):
        raise ValueError('Se requiere una cadena Oracle Cloud TCPS con servicio y verificación del servidor.') from None
    return parametros


def probar_conexion(parametros, usuario, clave):
    consulta = (RAIZ / 'sql/cloud/02_comprobar_conexion.sql').read_text(encoding='utf-8').strip().rstrip(';')
    with oracledb.connect(user=usuario, password=clave, params=parametros) as conn:
        with conn.cursor() as cur:
            cur.execute(consulta)
            fila = cur.fetchone()
        return {'usuario': fila[0], 'base_datos': fila[1], 'servicio': fila[2], 'version': conn.version}


def main():
    usar_entorno()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dsn-archivo', type=Path, default=RAIZ / '.local/oracle_cloud/dsn.txt')
    parser.add_argument('--usuario', default='ADMIN')
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument('--solo-validar', action='store_true', help='Revisar el descriptor sin usar la red.')
    modo.add_argument('--solo-red', action='store_true', help='Comprobar DNS y puerto; no autentica ni ejecuta SQL.')
    args = parser.parse_args()
    try:
        parametros = leer_parametros(args.dsn_archivo)
        if args.solo_validar:
            print('Descriptor Oracle Cloud válido: TCPS y verificación del servidor habilitados.')
            return
        if args.solo_red:
            if not isinstance(parametros.host, str) or not isinstance(parametros.port, int):
                raise ValueError('La prueba de red requiere un descriptor con una sola dirección.')
            with socket.create_connection((parametros.host, parametros.port), timeout=10):
                pass
            print('DNS y puerto TCPS accesibles. TLS, credenciales y consulta Oracle aún no comprobados.')
            return
        if not sys.stdin.isatty():
            raise ValueError('Ejecuta este comando en una terminal interactiva para escribir la contraseña sin mostrarla.')
        clave = getpass('Contraseña Oracle del usuario seleccionado (entrada oculta): ')
        if not clave:
            raise ValueError('No se introdujo una contraseña.')
        try:
            resultado = probar_conexion(parametros, args.usuario, clave)
        finally:
            clave = None
        carpeta = RAIZ / '.local/oracle_cloud'
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / 'ultima_comprobacion.json').write_text(json.dumps(resultado, indent=2), encoding='utf-8')
        print('Conexión TLS y consulta de solo lectura correctas.')
        print('Usuario:', resultado['usuario'], '| Oracle:', resultado['version'])
        print('Resultado privado: .local/oracle_cloud/ultima_comprobacion.json')
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    except oracledb.Error as exc:
        codigo = getattr(exc.args[0], 'full_code', '') if exc.args else ''
        sufijo = ' (' + codigo + ')' if re.fullmatch(r'(ORA|DPY|DPI)-\d+', codigo) else ''
        raise SystemExit('No se pudo completar la conexión Oracle' + sufijo + '. Revisa credenciales, cadena y ACL.') from None
    except OSError:
        raise SystemExit('No se pudo completar la operación de red o archivo. Revisa conectividad, ACL y permisos.') from None


if __name__ == '__main__':
    main()
