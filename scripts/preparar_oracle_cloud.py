"""Prepara cuentas y esquema en una Autonomous nueva; Oracle local permanece aparte."""
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
MIGRACIONES = (
    ('002', '002_auditoria.sql'), ('003', '003_clases.sql'),
    ('004', '004_estados_deteccion.sql'), ('005', '005_gestion.sql'),
    ('006', '006_administracion.sql'), ('007', '007_sesiones.sql'),
    ('008', '008_excepciones.sql'),
    ('009', '009_excepciones_docentes.sql'),
)


def consulta(nombre):
    return (RAIZ / 'sql/cloud/consultas' / nombre).read_text(encoding='utf-8').strip().rstrip(';')


def estado(fase, **datos):
    CARPETA.mkdir(parents=True, exist_ok=True)
    (CARPETA / 'instalacion.json').write_text(json.dumps({'fase': fase, **datos}, indent=2), encoding='utf-8')


def guardar_cuentas(dsn):
    config = {'ORACLE_USUARIO': 'UPC_ASISTENCIA', 'ORACLE_CONTRASENA': 'Oc9_' + secrets.token_hex(12),
              'ORACLE_ADMIN_USUARIO': 'UPC_ADMIN_APP', 'ORACLE_ADMIN_CONTRASENA': 'Oc9_' + secrets.token_hex(12),
              'ORACLE_DSN': dsn, 'ORACLE_TLS_MODO': 'tls',
              'ORACLE_POOL_MINIMO': 1, 'ORACLE_POOL_MAXIMO': 4,
              'ORACLE_ADMIN_POOL_MINIMO': 0, 'ORACLE_ADMIN_POOL_MAXIMO': 2}
    CARPETA.mkdir(parents=True, exist_ok=True)
    with CUENTAS.open('x', encoding='utf-8') as archivo:
        CUENTAS.chmod(0o600)
        archivo.write('# Privado. Conexiones tecnicas de cloud; no es la configuracion local de Streamlit.\n')
        for nombre, valor in config.items():
            archivo.write(nombre + ' = ' + json.dumps(valor) + '\n')
    return config


def validar_destino(config):
    if config.get('ORACLE_DSN') != (CARPETA / 'dsn.txt').read_text(encoding='utf-8').strip():
        raise ValueError('El descriptor difiere del registrado para estas cuentas. Revisar antes de continuar.')
    if config.get('ORACLE_USUARIO') != 'UPC_ASISTENCIA' or config.get('ORACLE_ADMIN_USUARIO') != 'UPC_ADMIN_APP':
        raise ValueError('Las cuentas no corresponden al aprovisionamiento cloud del proyecto.')


def migraciones_pendientes(versiones):
    conocidas = {'001', *(numero for numero, _ in MIGRACIONES)}
    if not versiones or versiones - conocidas or versiones != {f'{n:03d}' for n in range(1, len(versiones) + 1)}:
        raise ValueError('Se requiere una secuencia continua de versiones desde 001. No se repite el instalador inicial.')
    return [(numero, archivo) for numero, archivo in MIGRACIONES if numero not in versiones]


def continuar(parametros, config):
    validar_destino(config)
    avance = json.loads((CARPETA / 'instalacion.json').read_text(encoding='utf-8'))
    if avance.get('fase') not in {'usuarios_creados', 'instalacion_iniciada', 'migracion_en_curso', 'completada'}:
        raise ValueError('Revisar la preparación de cuentas antes de continuar el esquema.')
    with oracledb.connect(user=config['ORACLE_USUARIO'], password=config['ORACLE_CONTRASENA'], params=parametros) as conn:
        with conn.cursor() as cur:
            cur.execute(consulta('versiones.sql'))
            pendientes = migraciones_pendientes({fila[0] for fila in cur.fetchall()})
        for numero, archivo in pendientes:
            plan = list(leer_script(RAIZ / 'sql/migraciones' / archivo, RAIZ))
            estado('migracion_en_curso', version=numero)
            print('Continuando migración', numero, flush=True)
            ejecutar_script(conn, plan, informar=lambda paso: print('SQL:', paso, flush=True))
        if pendientes or avance.get('fase') != 'completada':
            ejecutar_script(conn, leer_script(RAIZ / 'sql/cloud/01_permisos_administracion.sql', RAIZ))
            conn.commit()
    verificar(parametros, config)


def verificar(parametros, config):
    validar_destino(config)
    with oracledb.connect(user=config['ORACLE_USUARIO'], password=config['ORACLE_CONTRASENA'], params=parametros) as conn:
        ejecutar_script(conn, leer_script(RAIZ / 'sql/cloud/04_verificar_instalacion.sql', RAIZ))
        with conn.cursor() as cur:
            cur.execute(consulta('inventario.sql'))
            inventario = dict(cur.fetchall())
    with oracledb.connect(user=config['ORACLE_ADMIN_USUARIO'], password=config['ORACLE_ADMIN_CONTRASENA'], params=parametros) as conn:
        ejecutar_script(conn, leer_script(RAIZ / 'sql/cloud/05_verificar_acceso_admin.sql', RAIZ))
    estado('completada', inventario=inventario)
    print('Esquema 001–009 verificado y acceso administrativo limitado correcto.')
    print('Inventario:', json.dumps(inventario, ensure_ascii=False))


def main():
    usar_entorno()
    parser = argparse.ArgumentParser(description=__doc__)
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument('--comprobar-plan', action='store_true', help='Leer y validar archivos SQL; no usar red.')
    modo.add_argument('--verificar', action='store_true', help='Comprobar una instalación creada, sin DDL ni ADMIN.')
    modo.add_argument('--continuar', action='store_true', help='Aplicar únicamente migraciones pendientes desde una 001 registrada; no recrea cuentas ni tablas iniciales.')
    args = parser.parse_args()
    try:
        parametros = leer_parametros(CARPETA / 'dsn.txt')
        instalacion = list(leer_script(RAIZ / 'oracle_scripts.sql', RAIZ))
        permisos = list(leer_script(RAIZ / 'sql/cloud/01_permisos_administracion.sql', RAIZ))
        creacion = list(leer_script(RAIZ / 'sql/cloud/03_aprovisionar_usuarios.sql', RAIZ))
        if args.comprobar_plan:
            print('Plan SQL válido:', len(instalacion), 'sentencias de instalación y', len(permisos), 'de permisos.')
            return
        if args.verificar:
            verificar(parametros, tomllib.loads(CUENTAS.read_text(encoding='utf-8')))
            return
        if args.continuar:
            continuar(parametros, tomllib.loads(CUENTAS.read_text(encoding='utf-8')))
            return
        if CUENTAS.exists():
            raise ValueError('Ya hay credenciales cloud preparadas. Usa --verificar o --continuar tras revisar instalacion.json; no se repite el instalador inicial.')
        if not sys.stdin.isatty():
            raise ValueError('Ejecuta en una terminal interactiva para introducir la contraseña de ADMIN.')
        clave = getpass('Contraseña ADMIN de Autonomous (entrada oculta): ')
        if not clave:
            raise ValueError('No se introdujo una contraseña.')
        try:
            with oracledb.connect(user='ADMIN', password=clave, params=parametros) as conn, conn.cursor() as cur:
                cur.execute(consulta('usuarios_proyecto.sql'))
                if cur.fetchall():
                    raise ValueError('Ya existe una cuenta del proyecto en esa base. No se reemplaza ni se borra.')
                config = guardar_cuentas((CARPETA / 'dsn.txt').read_text(encoding='utf-8').strip())
                estado('creacion_usuarios_iniciada')
                cur.execute(creacion[0].sql, clave_propietario=config['ORACLE_CONTRASENA'],
                            clave_administracion=config['ORACLE_ADMIN_CONTRASENA'])
        finally:
            clave = None
        estado('usuarios_creados')
        with oracledb.connect(user=config['ORACLE_USUARIO'], password=config['ORACLE_CONTRASENA'], params=parametros) as conn:
            with conn.cursor() as cur:
                cur.execute(consulta('objetos_propietario.sql'))
                if cur.fetchone()[0]:
                    raise ValueError('El propietario no está vacío. No se ejecutó la instalación inicial.')
            estado('instalacion_iniciada')
            ejecutar_script(conn, instalacion, informar=lambda paso: print('SQL:', paso, flush=True))
            ejecutar_script(conn, permisos, informar=lambda paso: print('SQL:', paso, flush=True))
            conn.commit()
        verificar(parametros, config)
        print('Credenciales técnicas privadas: .local/oracle_cloud/credenciales_tecnicas.toml')
        print('No se guardó la contraseña de ADMIN ni se cambió Oracle local.')
    except (ValueError, RuntimeError) as exc:
        # Solo los mensajes propios y las ubicaciones SQL, nunca SQL/passwords.
        codigo = getattr(getattr(exc, '__cause__', None), 'args', ())
        codigo = getattr(codigo[0], 'full_code', '') if codigo else ''
        sufijo = ' (' + codigo + ')' if re.fullmatch(r'(ORA|DPY|DPI)-\d+', codigo) else ''
        raise SystemExit(str(exc) + sufijo) from None
    except oracledb.Error as exc:
        codigo = getattr(exc.args[0], 'full_code', '') if exc.args else ''
        sufijo = ' (' + codigo + ')' if re.fullmatch(r'(ORA|DPY|DPI)-\d+', codigo) else ''
        raise SystemExit('Oracle no completó la preparación' + sufijo + '. Revisa el estado privado antes de repetir.') from None
    except OSError:
        raise SystemExit('No se pudo completar una operación de archivo. Revisa permisos y el estado privado.') from None


if __name__ == '__main__':
    main()
