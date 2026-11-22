"""Separa la cuenta de ejecución en Autonomous sin modificar Oracle ni secretos locales."""
import argparse
from getpass import getpass
import json
from pathlib import Path
import re
import secrets
import sys
import tomllib

import oracledb

from _comun import RAIZ, usar_entorno
from _scripts_sql import leer_script, ejecutar_script
from probar_oracle_cloud import leer_parametros

CARPETA = RAIZ / '.local/oracle_cloud'
CUENTAS = CARPETA / 'credenciales_tecnicas.toml'
EJECUCION = CARPETA / 'credenciales_ejecucion.toml'


def plan(nombre):
    return list(leer_script(RAIZ / 'sql/cloud' / nombre, RAIZ))


def validar_destino(config, *, ejecucion=False):
    if config.get('ORACLE_DSN') != (CARPETA / 'dsn.txt').read_text(encoding='utf-8').strip():
        raise ValueError('El descriptor no coincide con el destino cloud registrado; no se continúa.')
    esperado = 'UPC_AULA_APP' if ejecucion else 'UPC_ASISTENCIA'
    if config.get('ORACLE_USUARIO') != esperado or config.get('ORACLE_ADMIN_USUARIO') != 'UPC_ADMIN_APP':
        raise ValueError('Las cuentas no corresponden al proyecto cloud.')
    if ejecucion and config.get('ORACLE_ESQUEMA') != 'UPC_ASISTENCIA':
        raise ValueError('El propietario esperado es UPC_ASISTENCIA.')


def guardar_cuenta(propietario):
    config = {nombre: valor for nombre, valor in propietario.items()
        if nombre in ('ORACLE_DSN', 'ORACLE_TLS_MODO', 'ORACLE_POOL_MINIMO', 'ORACLE_POOL_MAXIMO',
            'ORACLE_ADMIN_USUARIO', 'ORACLE_ADMIN_CONTRASENA',
            'ORACLE_ADMIN_POOL_MINIMO', 'ORACLE_ADMIN_POOL_MAXIMO')}
    config.update(ORACLE_USUARIO='UPC_AULA_APP', ORACLE_ESQUEMA='UPC_ASISTENCIA',
        ORACLE_CONTRASENA='Ex9_' + secrets.token_hex(12))
    with EJECUCION.open('x', encoding='utf-8') as archivo:
        EJECUCION.chmod(0o600)
        archivo.write('# Privado. Ejecucion cloud; no sustituye secrets.toml del PC ni las credenciales del propietario.\n')
        for nombre, valor in config.items():
            archivo.write(nombre + ' = ' + json.dumps(valor) + '\n')
    return config


def verificar(parametros, config):
    from src.base_datos.permisos_ejecucion import comprobar_permisos
    validar_destino(config, ejecucion=True)
    with oracledb.connect(user=config['ORACLE_USUARIO'], password=config['ORACLE_CONTRASENA'], params=parametros) as conn:
        conn.current_schema = config['ORACLE_ESQUEMA']
        ejecutar_script(conn, plan('08_verificar_ejecucion.sql'))
        with conn.cursor() as cur:
            permisos = comprobar_permisos(cur, config['ORACLE_ESQUEMA'])
            cantidad = 0
            carpetas = ['base_datos/bd', 'base_datos/clases', 'base_datos/perfil_estudiante',
                'base_datos/administracion', 'servicios/recuperacion_acceso',
                'servicios/verificacion_identidad', 'servicios/sesiones_servidor', 'compartidas']
            for carpeta in carpetas:
                for archivo in sorted((RAIZ / 'sql/consultas' / carpeta).glob('*.sql')):
                    sql = archivo.read_text(encoding='utf-8')
                    if '{' in sql or not re.match(r'\s*(SELECT|WITH|INSERT|UPDATE|DELETE|BEGIN)\b', sql, re.I):
                        continue
                    # Cursor.parse no ejecuta DML/PLSQL. Nunca enviar DDL: parse lo ejecutaría.
                    try:
                        cur.parse(sql)
                    except oracledb.Error as exc:
                        raise RuntimeError('No se pudo analizar ' + archivo.relative_to(RAIZ).as_posix()) from exc
                    cantidad += 1
        conn.rollback()
    resultado = {'usuario': config['ORACLE_USUARIO'], 'esquema': config['ORACLE_ESQUEMA'],
        'permisos_verificados': permisos, 'consultas_analizadas_sin_ejecutar': cantidad,
        'objetos_propios': 0, 'verificado': True}
    (CARPETA / 'ejecucion_verificada.json').write_text(json.dumps(resultado, indent=2), encoding='utf-8')
    return resultado


def conceder(parametros, propietario):
    with oracledb.connect(user=propietario['ORACLE_USUARIO'],
            password=propietario['ORACLE_CONTRASENA'], params=parametros) as conn:
        ejecutar_script(conn, plan('07_permisos_ejecucion.sql'))


def main():
    usar_entorno()
    parser = argparse.ArgumentParser(description=__doc__)
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument('--comprobar-plan', action='store_true', help='Comprueba el SQL sin red ni credenciales.')
    modo.add_argument('--verificar', action='store_true', help='Consulta permisos y analiza sentencias sin ejecutar DML ni DDL.')
    modo.add_argument('--continuar', action='store_true', help='Reaplica permisos a la cuenta ya creada y autenticada; nunca cambia su clave.')
    args = parser.parse_args()
    fase = 'validación de la preparación'
    try:
        creacion = plan('06_crear_usuario_ejecucion.sql')
        permisos = plan('07_permisos_ejecucion.sql')
        plan('08_verificar_ejecucion.sql')
        if args.comprobar_plan:
            from src.base_datos.permisos_ejecucion import contrato_permisos
            print('Plan válido:', len(creacion), 'bloque de creación,', len(permisos),
                'sentencias de permisos y', len(contrato_permisos()), 'permisos de objeto/columna.')
            return
        propietario = tomllib.loads(CUENTAS.read_text(encoding='utf-8'))
        validar_destino(propietario)
        parametros = leer_parametros(CARPETA / 'dsn.txt')
        if args.verificar or args.continuar:
            config = tomllib.loads(EJECUCION.read_text(encoding='utf-8'))
            validar_destino(config, ejecucion=True)
            if args.continuar:
                # Probar la clave original antes de conceder; no apropiarse de otra cuenta existente.
                fase = 'autenticación de UPC_AULA_APP'
                with oracledb.connect(user=config['ORACLE_USUARIO'], password=config['ORACLE_CONTRASENA'], params=parametros):
                    pass
                fase = 'concesión de permisos desde UPC_ASISTENCIA'
                conceder(parametros, propietario)
            fase = 'verificación de UPC_AULA_APP'
            resultado = verificar(parametros, config)
        else:
            if EJECUCION.exists():
                raise ValueError('Ya hay credenciales de ejecución. Usa --verificar o --continuar; no se reemplaza la cuenta.')
            if not sys.stdin.isatty():
                raise ValueError('Ejecuta en una terminal interactiva para introducir ADMIN sin eco.')
            clave = getpass('Contraseña ADMIN de Autonomous (entrada oculta; no se guarda): ')
            if not clave:
                raise ValueError('No se introdujo una contraseña.')
            try:
                fase = 'autenticación de ADMIN'
                with oracledb.connect(user='ADMIN', password=clave, params=parametros) as conn, conn.cursor() as cur:
                    fase = 'comprobación de cuentas con ADMIN'
                    cur.execute((RAIZ / 'sql/cloud/consultas/usuario_ejecucion.sql').read_text(encoding='utf-8'))
                    if cur.fetchone()[0]:
                        raise ValueError('UPC_AULA_APP ya existe; no se cambió su contraseña ni se generaron credenciales.')
                    # Persistir antes del DDL: si hay un fallo, se conserva la clave original.
                    config = guardar_cuenta(propietario)
                    fase = 'creación de UPC_AULA_APP'
                    cur.execute(creacion[0].sql, clave_ejecucion=config['ORACLE_CONTRASENA'])
            finally:
                clave = None
            fase = 'concesión de permisos desde UPC_ASISTENCIA'
            conceder(parametros, propietario)
            fase = 'verificación de UPC_AULA_APP'
            resultado = verificar(parametros, config)
        print('Cuenta de ejecución comprobada:', json.dumps(resultado, ensure_ascii=False))
        print('Configuración privada: .local/oracle_cloud/credenciales_ejecucion.toml')
        print('No se cambió Oracle local ni .streamlit/secrets.toml; ADMIN no se guardó.')
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from None
    except oracledb.Error as exc:
        codigo = getattr(exc.args[0], 'full_code', '') if exc.args else ''
        sufijo = ' (' + codigo + ')' if re.fullmatch(r'(ORA|DPY|DPI)-\d+', codigo) else ''
        if codigo == 'ORA-01017' and fase == 'autenticación de ADMIN':
            raise SystemExit('Oracle rechazó el acceso de ADMIN (ORA-01017). Revisa la contraseña ADMIN '
                'definida para Autonomous UPCAULA. Esta ejecución no creó usuarios ni guardó credenciales nuevas.') from None
        raise SystemExit('Oracle no completó la fase: ' + fase + sufijo +
            '. Conserva los archivos privados; no se restablece ninguna clave.') from None
    except OSError:
        raise SystemExit('No se pudo leer o guardar la configuración privada de ejecución.') from None


if __name__ == '__main__':
    main()
