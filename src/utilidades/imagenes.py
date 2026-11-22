"""Lectura acotada de fotos y deduplicación por contenido dentro de la toma vigente."""

from hashlib import sha256
from io import BytesIO
from contextlib import contextmanager
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError
import streamlit as st

from src.utilidades.sesiones import contexto_vigente, invalidar_resultado

MAX_FOTOS = 12
MAX_BYTES_FOTO = 10 * 1024 * 1024
MAX_BYTES_TOMA = 60 * 1024 * 1024
MAX_PIXELES_FOTO = 20_000_000
MAX_LADO_MINIATURA = 480


@dataclass(frozen=True)
class FotoAsistencia:
    """Original comprimido para analizar y miniatura independiente para mostrar."""
    datos: bytes
    miniatura: bytes


def _validar_original(original):
    if original.format not in ('JPEG', 'PNG'):
        raise ValueError('La fotografía debe ser JPEG o PNG.')
    if original.width * original.height > MAX_PIXELES_FOTO:
        raise ValueError('Cada fotografía puede tener como máximo 20 megapíxeles.')


def vista_previa_foto(foto):
    return foto.miniatura if isinstance(foto, FotoAsistencia) else foto


@contextmanager
def abrir_foto(foto):
    """Decodifica una foto a su resolución original y libera su imagen al terminar."""
    if isinstance(foto, Image.Image):
        # Compatibilidad con tomas ya abiertas antes de actualizar el código.
        imagen = foto.convert('RGB')
        try:
            yield imagen
        finally:
            imagen.close()
        return
    datos = foto.datos if isinstance(foto, FotoAsistencia) else foto
    try:
        with Image.open(BytesIO(datos)) as original:
            _validar_original(original)
            ImageOps.exif_transpose(original, in_place=True)
            imagen = original.convert('RGB')
            try:
                imagen.load()
                yield imagen
            finally:
                imagen.close()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('No se pudo leer la fotografía. Comprueba que sea una imagen válida.') from exc


def agregar_foto(archivo, contexto, estado=None):
    estado = st.session_state if estado is None else estado
    if not contexto_vigente(contexto, estado):
        raise PermissionError("La sesión o materia cambió. Abre nuevamente la captura de fotos.")
    datos = archivo.getvalue()
    if not datos or len(datos) > MAX_BYTES_FOTO:
        raise ValueError("Cada fotografía debe tener contenido y ocupar como máximo 10 MB.")
    huella = sha256(datos).hexdigest()
    if huella in estado["claves_subidas_procesadas"]:
        return False
    if len(estado["imagenes_asistencia"]) >= MAX_FOTOS:
        raise ValueError("Puedes agregar hasta 12 fotografías por toma.")
    total = estado.get("bytes_imagenes_asistencia", 0) + len(datos)
    if total > MAX_BYTES_TOMA:
        raise ValueError("Las fotografías de una toma pueden ocupar como máximo 60 MB.")
    try:
        with Image.open(BytesIO(datos)) as original:
            _validar_original(original)
            # Validar toda la captura, pero conservar solo sus bytes comprimidos.
            original.load()
            ImageOps.exif_transpose(original, in_place=True)
            original.thumbnail((MAX_LADO_MINIATURA, MAX_LADO_MINIATURA))
            with original.convert('RGB') as miniatura:
                salida = BytesIO()
                miniatura.save(salida, format='JPEG', quality=85)
                foto = FotoAsistencia(datos, salida.getvalue())
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("No se pudo leer la fotografía. Comprueba que sea una imagen válida.") from exc
    estado["imagenes_asistencia"].append(foto)
    estado["claves_subidas_procesadas"].add(huella)
    estado["bytes_imagenes_asistencia"] = total
    invalidar_resultado(estado)
    return True
