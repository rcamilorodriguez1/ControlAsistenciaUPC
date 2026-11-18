from threading import Lock

import oracledb

from src.configuracion import obtener_configuracion as _obtener_configuracion


ORACLE_USUARIO = _obtener_configuracion("ORACLE_USUARIO", "UPC_ASISTENCIA")
ORACLE_CONTRASENA = _obtener_configuracion("ORACLE_CONTRASENA")
ORACLE_DSN = _obtener_configuracion("ORACLE_DSN", "localhost:1521/XEPDB1")
ORACLE_POOL_MINIMO = int(_obtener_configuracion("ORACLE_POOL_MINIMO", 1))
ORACLE_POOL_MAXIMO = int(_obtener_configuracion("ORACLE_POOL_MAXIMO", 10))

# El modo "thin" de python-oracledb es puro Python y NO requiere tener
# instalado el Oracle Instant Client en la maquina.
oracledb.defaults.fetch_lobs = False  # Las columnas CLOB/BLOB se devuelven directo como str/bytes

_grupo_conexiones = None
_bloqueo_pool = Lock()


def obtener_pool():
    global _grupo_conexiones
    if not ORACLE_USUARIO or not ORACLE_CONTRASENA or not ORACLE_DSN:
        raise ValueError(
            "Falta configurar Oracle. Ejecuta scripts/preparar_oracle.py o define "
            "ORACLE_USUARIO, ORACLE_CONTRASENA y ORACLE_DSN en el entorno "
            "o en .streamlit/secrets.toml."
        )
    if ORACLE_POOL_MINIMO < 0 or ORACLE_POOL_MAXIMO < max(1, ORACLE_POOL_MINIMO):
        raise ValueError("El pool requiere 0 <= ORACLE_POOL_MINIMO <= ORACLE_POOL_MAXIMO y máximo >= 1.")
    with _bloqueo_pool:
        if _grupo_conexiones is None:
            _grupo_conexiones = oracledb.create_pool(
                user=ORACLE_USUARIO,
                password=ORACLE_CONTRASENA,
                dsn=ORACLE_DSN,
                min=ORACLE_POOL_MINIMO,
                max=ORACLE_POOL_MAXIMO,
                increment=1,
            )
    return _grupo_conexiones


def obtener_conexion():
    """Obtiene una conexión del pool hacia Oracle Express XE 18c."""
    return obtener_pool().acquire()
