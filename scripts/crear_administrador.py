"""Alta explícita de la primera cuenta web, sin SYSDBA ni cambios a usuarios Oracle."""
import argparse
from getpass import getpass
import os
from pathlib import Path
import tomllib

from _comun import usar_entorno


def crear_cuenta(usuario, nombre, clave):
    from src.base_datos.esquema import esquema_propietario
    from src.configuracion import obtener_configuracion
    if str(obtener_configuracion('ORACLE_USUARIO', 'UPC_ASISTENCIA')).upper() != esquema_propietario():
        raise ValueError('El alta inicial requiere el propietario. Usa --config-oracle con su perfil privado; no concedas INSERT en administradores al runtime.')
    from src.base_datos.configuracion import obtener_conexion
    from src.base_datos.bd import cifrar_contrasena
    from src.servicios.validaciones import usuario as validar_usuario, texto, clave as validar_clave
    from src.servicios.seguridad_claves import evaluar_clave
    usuario = validar_usuario(usuario)
    nombre = texto(nombre, 'Nombre', 200)
    validar_clave(clave)
    if evaluar_clave(clave, usuario=usuario, nombre=nombre).puntuacion < 3:
        raise ValueError('Elige una contraseña fuerte o muy fuerte para administración.')
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM administradores')
        if cur.fetchone()[0]:
            raise ValueError('Ya existe una cuenta administrativa; utiliza la gestión existente. No se cambió ninguna contraseña.')
        cur.execute('INSERT INTO administradores(usuario,nombre,contrasena) VALUES(:u,:n,:c)',
                    u=usuario, n=nombre, c=cifrar_contrasena(clave))
        cur.execute("""INSERT INTO eventos_gestion(entidad,entidad_id,accion,motivo,actor_rol)
            SELECT 'ADMINISTRADOR',administrador_id,'ALTA','Alta inicial explícita de despliegue','SISTEMA'
            FROM administradores WHERE usuario=:u""", u=usuario)
        conn.commit()


def main():
    usar_entorno()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--usuario', required=True)
    parser.add_argument('--nombre', required=True)
    parser.add_argument('--config-oracle', type=Path, help='Perfil privado del propietario; no modifica secrets.toml.')
    args = parser.parse_args()
    if args.config_oracle:
        config = tomllib.loads(args.config_oracle.read_text(encoding='utf-8'))
        for nombre, valor in config.items():
            if nombre.startswith('ORACLE_'):
                os.environ[nombre] = str(valor)
        os.environ['ORACLE_ESQUEMA'] = str(config.get('ORACLE_ESQUEMA', config['ORACLE_USUARIO']))
    clave = getpass('Contraseña de la cuenta web (no se mostrará): ')
    if getpass('Confirmación: ') != clave:
        parser.error('Las contraseñas no coinciden.')
    try:
        crear_cuenta(args.usuario, args.nombre, clave)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    except Exception as exc:
        raise SystemExit('No se pudo crear la cuenta (' + type(exc).__name__ + '). Revisa Oracle antes de repetir.') from None
    print('Primera cuenta web creada y auditada. No se guardó la contraseña en archivos ni logs.')


if __name__ == '__main__':
    main()
