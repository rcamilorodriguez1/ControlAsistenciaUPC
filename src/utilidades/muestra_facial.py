"""Lectura acotada de la captura de acceso/registro; no conserva el archivo original."""

from io import BytesIO

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from src.utilidades.biometria import MuestraInvalida

MAX_BYTES_REGISTRO = 10 * 1024 * 1024
MAX_PIXELES = 20_000_000
MIN_LADO = 96
MIN_LADO_ROSTRO = 80


def validar_imagen_rgb(imagen):
    matriz = np.asarray(imagen)
    if matriz.dtype != np.uint8 or matriz.ndim != 3 or matriz.shape[2] != 3:
        raise MuestraInvalida('La imagen debe ser RGB con píxeles de 8 bits.', 'IMAGEN_INVALIDA')
    alto, ancho = matriz.shape[:2]
    if min(alto, ancho) < MIN_LADO or alto * ancho > MAX_PIXELES:
        raise MuestraInvalida('Usa una imagen de al menos 96 × 96 píxeles y hasta 20 megapíxeles.', 'TAMANO_IMAGEN')
    return np.ascontiguousarray(matriz)


def leer_foto_registro(archivo):
    if not hasattr(archivo, 'getvalue'):
        raise MuestraInvalida('Captura una fotografía antes de continuar.', 'IMAGEN_INVALIDA')
    datos = archivo.getvalue()
    if not isinstance(datos, bytes) or not datos or len(datos) > MAX_BYTES_REGISTRO:
        raise MuestraInvalida('La fotografía debe tener contenido y ocupar como máximo 10 MB.', 'TAMANO_IMAGEN')
    try:
        with Image.open(BytesIO(datos)) as original:
            if original.format not in ('JPEG', 'PNG'):
                raise MuestraInvalida('La fotografía debe ser JPEG o PNG.', 'FORMATO_IMAGEN')
            if original.width * original.height > MAX_PIXELES or min(original.size) < MIN_LADO:
                raise MuestraInvalida('Usa una imagen de al menos 96 × 96 píxeles y hasta 20 megapíxeles.', 'TAMANO_IMAGEN')
            imagen = ImageOps.exif_transpose(original).convert('RGB')
            imagen.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise MuestraInvalida('No se pudo leer la fotografía. Captúrala nuevamente.', 'IMAGEN_INVALIDA') from exc
    return validar_imagen_rgb(imagen)
