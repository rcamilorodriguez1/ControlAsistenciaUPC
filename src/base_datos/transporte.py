"""Transporte compartido de los dos pools: Oracle local, TLS o wallet mTLS."""
from pathlib import Path

import oracledb

from src.configuracion import obtener_configuracion


def parametros_transporte():
    modo = str(obtener_configuracion('ORACLE_TLS_MODO', 'local')).lower()
    if modo == 'local':
        return {}
    if modo not in {'tls', 'mtls'}:
        raise ValueError('ORACLE_TLS_MODO debe ser local, tls o mtls.')
    opciones = {'ssl_server_dn_match': True, 'tcp_connect_timeout': 15}
    if modo == 'mtls':
        carpeta = obtener_configuracion('ORACLE_WALLET_DIRECTORIO')
        clave = obtener_configuracion('ORACLE_WALLET_CONTRASENA')
        if not carpeta or not clave:
            raise ValueError('mTLS requiere directorio y contraseña del wallet Oracle.')
        ruta = Path(carpeta)
        if not all((ruta / nombre).is_file() for nombre in ('tnsnames.ora', 'ewallet.pem')):
            raise ValueError('El wallet requiere tnsnames.ora y ewallet.pem.')
        opciones.update(config_dir=str(ruta), wallet_location=str(ruta), wallet_password=clave)
    # Resolver también los alias: cada dirección de un descriptor debe usar TCPS.
    # No se abre una conexión ni se incluye el DSN en mensajes de error.
    try:
        parametros = oracledb.ConnectParams(config_dir=opciones.get('config_dir'))
        parametros.parse_connect_string(obtener_configuracion('ORACLE_DSN', ''))
        protocolos = parametros.protocol
        if not isinstance(protocolos, list):
            protocolos = [protocolos]
        if not protocolos or any(p != 'tcps' for p in protocolos) or not parametros.ssl_server_dn_match:
            raise ValueError
    except (oracledb.Error, ValueError, TypeError):
        raise ValueError('Oracle Cloud requiere un DSN TCPS válido y verificación del servidor habilitada.') from None
    return opciones
