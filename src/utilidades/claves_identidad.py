"""Lectura de la misma clave de identidad en formato binario o Base64."""
import base64
import binascii
from pathlib import Path


def leer_clave(ruta, formato='binario'):
    if formato not in ('binario', 'base64'):
        raise ValueError('IDENTIDAD_CLAVE_FORMATO debe ser binario o base64.')
    try:
        datos = Path(ruta).read_bytes()
        if formato == 'base64':
            datos = base64.b64decode(datos.strip(), validate=True)
    except (OSError, binascii.Error, ValueError):
        raise ValueError('No se pudo leer la clave de identidad original.') from None
    if len(datos) != 32:
        raise ValueError('La clave de identidad original debe contener 32 bytes.')
    return datos
