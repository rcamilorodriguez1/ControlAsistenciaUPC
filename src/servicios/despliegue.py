"""Comprobaciones de producción sin crear usuarios, claves ni objetos Oracle."""
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from src.configuracion import obtener_configuracion
from src.base_datos.transporte import parametros_transporte
from src.base_datos.consultas import cargar_sql, sql_con_identificadores


def validar_configuracion():
    requeridos = ('APP_BASE_URL', 'ORACLE_USUARIO', 'ORACLE_CONTRASENA', 'ORACLE_DSN',
                  'ORACLE_ADMIN_USUARIO', 'ORACLE_ADMIN_CONTRASENA', 'PROFESOR_CLAVE_ALTA',
                  'IDENTIDAD_CLAVE_RUTA')
    for nombre in requeridos:
        valor = obtener_configuracion(nombre)
        if not isinstance(valor, str) or not valor.strip() or valor.startswith(('REEMPLAZAR', 'CAMBIAR')):
            raise ValueError(f'Falta definir {nombre} para producción.')
    try:
        url = urlsplit(obtener_configuracion('APP_BASE_URL'))
        host = url.hostname or ''
        if (url.scheme != 'https' or url.username is not None or url.password is not None
                or url.path not in ('', '/') or url.query or url.fragment
                or url.port not in (None, 443)
                or not re.fullmatch(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}', host)
                or host.endswith(('.localhost', '.local', '.invalid'))):
            raise ValueError
    except ValueError:
        raise ValueError('APP_BASE_URL debe ser https:// seguido de un dominio público, sin subruta ni puerto alternativo.') from None
    usuarios = [obtener_configuracion(n).upper() for n in ('ORACLE_USUARIO', 'ORACLE_ADMIN_USUARIO')]
    if len(set(usuarios)) != 2 or any(u in {'SYS', 'SYSTEM', 'ADMIN'} for u in usuarios):
        raise ValueError('Usa dos cuentas Oracle del proyecto distintas; ADMIN/SYS/SYSTEM no son cuentas de ejecución.')
    if obtener_configuracion('ORACLE_TLS_MODO') not in ('tls', 'mtls'):
        raise ValueError('En producción ORACLE_TLS_MODO debe ser tls o mtls.')
    parametros_transporte()
    for prefijo, minimo, maximo in (('ORACLE', 1, 10), ('ORACLE_ADMIN', 0, 4)):
        try:
            inferior = int(obtener_configuracion(prefijo + '_POOL_MINIMO', minimo))
            superior = int(obtener_configuracion(prefijo + '_POOL_MAXIMO', maximo))
            if inferior < 0 or superior < max(1, inferior):
                raise ValueError
        except (ValueError, TypeError):
            raise ValueError(f'Revisa los límites de {prefijo}_POOL.') from None
    # Leer la clave original; el arranque nunca genera ni reemplaza una clave.
    try:
        ruta = Path(obtener_configuracion('IDENTIDAD_CLAVE_RUTA'))
        if not ruta.is_absolute() or len(ruta.read_bytes()) != 32:
            raise ValueError
    except (OSError, ValueError):
        raise ValueError('Falta la clave de identidad original de 32 bytes en una ruta absoluta legible.') from None
    return host


def comprobar_base():
    from src.base_datos.configuracion import obtener_conexion
    from src.base_datos.administracion import obtener_pool_admin, propietario
    with obtener_conexion() as conn, conn.cursor() as cur:
        cur.execute(cargar_sql('servicios/despliegue/comprobar_base_01'))
        versiones = {r[0] for r in cur}
        if not {f'{n:03d}' for n in range(1, 9)} <= versiones:
            raise ValueError('Instala y verifica el esquema 001–008 antes de iniciar.')
        cur.execute(cargar_sql('servicios/despliegue/comprobar_base_02'))
        if cur.fetchone()[0]:
            raise ValueError('El esquema contiene objetos inválidos.')
        cur.execute(cargar_sql('servicios/despliegue/comprobar_base_03'))
        if cur.fetchone()[0]:
            raise ValueError('El esquema contiene disparadores deshabilitados.')
    with obtener_pool_admin().acquire() as conn, conn.cursor() as cur:
        for vista in ('v_auditoria_asistencia', 'v_historial_matriculas', 'v_eventos_gestion'):
            cur.execute(sql_con_identificadores('servicios/despliegue/comprobar_vista', esquema=propietario(), vista=vista))
        cur.execute(cargar_sql('servicios/despliegue/comprobar_base_04'),
            esquema=obtener_configuracion('ORACLE_USUARIO').upper())
        if cur.fetchone()[0] != 4:
            raise ValueError('Faltan permisos EXECUTE de la cuenta administrativa limitada.')


def comando_streamlit(host):
    return [sys.executable, '-m', 'streamlit', 'run', 'principal.py',
            '--server.address=0.0.0.0', '--server.port=8501', '--server.headless=true',
            '--server.runOnSave=false', '--server.fileWatcherType=none',
            '--server.enableCORS=true', '--server.enableXsrfProtection=true',
            '--server.baseUrlPath=', '--server.sslCertFile=', '--server.sslKeyFile=',
            '--browser.serverAddress=' + host, '--browser.serverPort=443',
            '--browser.gatherUsageStats=false', '--client.showErrorDetails=none']
