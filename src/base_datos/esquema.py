"""Distingue el propietario de los objetos de la cuenta que abre la conexión."""
import re

from src.configuracion import obtener_configuracion


def esquema_propietario():
    # Compatibilidad con instalaciones locales que aún conectan como propietario.
    valor = obtener_configuracion('ORACLE_ESQUEMA',
        obtener_configuracion('ORACLE_USUARIO', 'UPC_ASISTENCIA'))
    if not isinstance(valor, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,29}', valor):
        raise ValueError('ORACLE_ESQUEMA debe ser un identificador Oracle simple de hasta 30 caracteres.')
    return valor.upper()


def iniciar_sesion(conexion, requested_tag=None):
    # CURRENT_SCHEMA resuelve los nombres; no concede permisos ni cambia SESSION_USER.
    conexion.current_schema = esquema_propietario()
