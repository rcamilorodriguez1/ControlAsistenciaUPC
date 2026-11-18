"""Ejecuta scripts SQL*Plus como usuario de la app, usando la configuracion local."""

import argparse
import re
import shutil

from _comun import RAIZ, usar_entorno
from preparar_oracle import ejecutar_sqlplus, identificador


def main():
    usar_entorno()
    from src.configuracion import obtener_configuracion
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accion', choices=['instalar', 'migrar', 'respaldar', 'verificar', 'demostrar', 'demostrar-disparadores', 'demostrar-clases', 'demostrar-estados', 'exportar'])
    args = parser.parse_args()
    if args.accion in ('migrar', 'respaldar'):
        from respaldo_oracle import respaldar
        print('Respaldo privado verificado:', respaldar().relative_to(RAIZ))
        if args.accion == 'respaldar':
            return
    sqlplus = shutil.which('sqlplus')
    if not sqlplus:
        parser.error('No se encontro SQL*Plus en PATH.')
    usuario = identificador(obtener_configuracion('ORACLE_USUARIO', 'UPC_ASISTENCIA'))
    clave = obtener_configuracion('ORACLE_CONTRASENA')
    dsn = obtener_configuracion('ORACLE_DSN', 'localhost:1521/XEPDB1')
    if not clave or any(c in clave for c in '\r\n'):
        parser.error('Configura una contrasena de Oracle valida en secrets.toml o el entorno.')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+:\d{1,5}/[A-Za-z0-9_.-]+', dsn):
        parser.error('Usa un DSN host:puerto/servicio.')
    rutas = {'instalar': 'oracle_scripts.sql', 'verificar': 'sql/04_verificar.sql',
             'demostrar': 'sql/05_demostracion.sql', 'exportar': 'sql/06_exportar_ddl.sql',
             'migrar': 'sql/migraciones/008_excepciones.sql',
             'demostrar-clases': 'sql/17_demostracion_clases.sql',
             'demostrar-estados': 'sql/22_demostracion_estados.sql',
             'demostrar-disparadores': 'sql/12_demostracion_disparadores.sql'}
    if args.accion == 'exportar':
        (RAIZ / 'exports').mkdir(exist_ok=True)
    pre_migracion = ''
    if args.accion == 'migrar':
        from src.base_datos.configuracion import obtener_conexion
        with obtener_conexion() as conn, conn.cursor() as cur:
            cur.execute('SELECT version FROM versiones_esquema')
            versiones = {f[0] for f in cur}
        if '001' not in versiones:
            parser.error('Se requiere la instalacion inicial 001 antes de migrar.')
        if '002' not in versiones:
            pre_migracion = f'@"{(RAIZ / "sql/migraciones/002_auditoria.sql").as_posix()}"\n'
        if '003' not in versiones:
            pre_migracion += f'@"{(RAIZ / "sql/migraciones/003_clases.sql").as_posix()}"\n'
        if '004' not in versiones:
            pre_migracion += f'@"{(RAIZ / "sql/migraciones/004_estados_deteccion.sql").as_posix()}"\n'
        if '005' not in versiones:
            pre_migracion += f'@"{(RAIZ / "sql/migraciones/005_gestion.sql").as_posix()}"\n'
        if '006' not in versiones:
            pre_migracion += '@sql/migraciones/006_administracion.sql\n'
        if '007' not in versiones:
            pre_migracion += '@sql/migraciones/007_sesiones.sql\n'
    post_migracion = ''
    if args.accion in ('migrar','instalar') and obtener_configuracion('ORACLE_ADMIN_ROL'):
        rol_admin = identificador(obtener_configuracion('ORACLE_ADMIN_ROL'))
        post_migracion = f'GRANT EXECUTE ON pkg_sesiones TO {rol_admin};\n'
        post_migracion += f'GRANT EXECUTE ON pkg_excepciones TO {rol_admin};\n'
    if args.accion in ('migrar','instalar'):
        from src.servicios.verificacion_identidad import preparar_clave
        preparar_clave()
    contenido = ('SET ECHO OFF\nSET VERIFY OFF\nWHENEVER OSERROR EXIT FAILURE\n'
                 'WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK\n'
                 f'CONNECT {usuario}@"//{dsn}"\n{clave}\n'
                 + pre_migracion + f'@"{(RAIZ / rutas[args.accion]).as_posix()}"\n' + post_migracion + 'EXIT SUCCESS\n')
    try:
        ejecutar_sqlplus(sqlplus, contenido, [clave])
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == '__main__':
    main()
