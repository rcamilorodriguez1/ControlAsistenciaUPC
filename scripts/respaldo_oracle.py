"""Respaldo privado v2, cifrado y autenticado; no imprime datos ni claves."""
from datetime import datetime, timezone
from uuid import uuid4
from _comun import RAIZ


def respaldar():
    from src.base_datos.configuracion import obtener_conexion
    from src.base_datos.recuperacion import respaldar as crear, clave_local
    clave = clave_local(RAIZ / '.local/clave_respaldos.bin', crear=True)
    destino = RAIZ / '.local/respaldos' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8])
    with obtener_conexion() as conexion:
        return crear(conexion,destino,clave)
