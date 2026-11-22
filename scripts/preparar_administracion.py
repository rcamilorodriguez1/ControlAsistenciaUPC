"""Preparar conexión Oracle limitada y primera cuenta administrativa privada."""
import argparse
import json
import re
import secrets
import shutil
import tomllib
from _comun import RAIZ, usar_entorno
from preparar_oracle import ejecutar_sqlplus, identificador


def main():
    usar_entorno()
    from src.base_datos.configuracion import obtener_conexion
    from src.base_datos.bd import cifrar_contrasena
    from src.servicios.validaciones import usuario as validar_usuario, texto
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--usuario', default='admin.upc')
    parser.add_argument('--nombre', default='Administración UPC')
    parser.add_argument('--usuario-oracle', type=identificador, default='UPC_ADMIN_APP')
    parser.add_argument('--rol-oracle', type=identificador, default='UPC_ROL_ADMIN')
    args = parser.parse_args()
    usuario = validar_usuario(args.usuario); nombre = texto(args.nombre, 'Nombre', 200)
    archivo = RAIZ / '.streamlit/secrets.toml'
    config = tomllib.loads(archivo.read_text(encoding='utf-8'))
    propietario = identificador(config['ORACLE_USUARIO'])
    dsn = config['ORACLE_DSN']
    if not re.fullmatch(r'(localhost|127\.0\.0\.1):\d+/[A-Za-z][A-Za-z0-9_]*', dsn):
        parser.error('La preparación automática requiere Oracle local; en otro servidor ejecutar el script con el DBA.')
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM versiones_esquema WHERE version='009'")
        if cur.fetchone()[0] != 1: parser.error('Instalar la migración 009 primero.')
    if 'ORACLE_ADMIN_USUARIO' not in config:
        pendiente = RAIZ / '.local/provision_admin_pendiente.json'
        if pendiente.exists(): parser.error('Existe una preparación pendiente; revisar ese archivo privado y el estado Oracle antes de repetir.')
        clave_db = 'Adb_' + secrets.token_hex(12)
        acceso = {'ORACLE_ADMIN_USUARIO': args.usuario_oracle, 'ORACLE_ADMIN_CONTRASENA': clave_db,
                  'ORACLE_ADMIN_ROL': args.rol_oracle}
        pendiente.write_text(json.dumps(acceso), encoding='utf-8'); pendiente.chmod(0o600)
        sqlplus = shutil.which('sqlplus')
        if not sqlplus: parser.error('SQLPlus no está en PATH.')
        pdb = identificador(dsn.split('/')[-1])
        contenido = ('SET ECHO OFF\nSET VERIFY OFF\nWHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK\n'
            f'CONNECT / AS SYSDBA\nALTER SESSION SET CONTAINER={pdb};\n@sql/30_permisos_administracion.sql\n'
            f'{propietario}\n{args.usuario_oracle}\n{args.rol_oracle}\n{clave_db}\nEXIT SUCCESS\n')
        ejecutar_sqlplus(sqlplus, contenido, [clave_db])
        with archivo.open('a', encoding='utf-8') as f:
            f.write('\n# Conexión administrativa limitada, preparada localmente.\n')
            for key, valor in acceso.items(): f.write(key + ' = ' + json.dumps(valor) + '\n')
        config.update(acceso)
        pendiente.unlink()
    privado = RAIZ / '.local/ADMINISTRADOR.md'
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute('SELECT administrador_id FROM administradores WHERE LOWER(TRIM(usuario))=:u', u=usuario)
        if cur.fetchone():
            print('La cuenta ya existe; no se cambió su contraseña. Credenciales locales:', privado.relative_to(RAIZ))
            return
        if privado.exists(): parser.error('Ya existe ADMINISTRADOR.md; no se sobrescribió ni se creó otra cuenta.')
        clave_app = 'Adm_' + secrets.token_urlsafe(18)
        privado.write_text('# Acceso administrativo local — privado\n\n'
            f'- Aplicación: https://localhost:8501 → Administración\n- Usuario: `{usuario}`\n- Contraseña: `{clave_app}`\n\n'
            'No publicar este archivo. La contraseña es de la aplicación; la conexión Oracle limitada está en secrets.toml.\n', encoding='utf-8')
        privado.chmod(0o600)
        cur.execute('INSERT INTO administradores(usuario,nombre,contrasena) VALUES(:u,:n,:c)', u=usuario,n=nombre,c=cifrar_contrasena(clave_app))
        cur.execute("""INSERT INTO eventos_gestion(entidad,entidad_id,accion,motivo,actor_rol)
            SELECT 'ADMINISTRADOR',administrador_id,'ALTA','Alta local mediante herramienta privada','SISTEMA'
            FROM administradores WHERE usuario=:u""", u=usuario)
        conn.commit()
    print('Acceso preparado. Credenciales privadas:', privado.relative_to(RAIZ))


if __name__ == '__main__': main()
