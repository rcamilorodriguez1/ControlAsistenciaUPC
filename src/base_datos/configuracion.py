import os
import streamlit as st
import oracledb


def _obtener_configuracion(clave, valor_por_defecto=None):
    try:
        if clave in st.secrets:
            return st.secrets[clave]
    except Exception:
        pass
    return os.environ.get(clave, valor_por_defecto)


ORACLE_USUARIO = _obtener_configuracion("ORACLE_USUARIO", "oscar")
ORACLE_CONTRASENA = _obtener_configuracion("ORACLE_CONTRASENA", "Contrasena.123")  # (contraseña estándar: cámbiala por la tuya)
ORACLE_DSN = _obtener_configuracion("ORACLE_DSN", "localhost:1521/XEPDB1")
ORACLE_POOL_MINIMO = int(_obtener_configuracion("ORACLE_POOL_MINIMO", 1))
ORACLE_POOL_MAXIMO = int(_obtener_configuracion("ORACLE_POOL_MAXIMO", 10))

# El modo "thin" de python-oracledb es puro Python y NO requiere tener
# instalado el Oracle Instant Client en la maquina.
oracledb.defaults.fetch_lobs = False  # Las columnas CLOB/BLOB se devuelven directo como str/bytes

_grupo_conexiones = None


def obtener_pool():
    global _grupo_conexiones
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
