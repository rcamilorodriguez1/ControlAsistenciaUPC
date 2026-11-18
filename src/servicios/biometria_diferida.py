"""Cargar IA solo al analizar una captura; mantener el inicio y los formularios ligeros."""
import sys


def predecir_asistencia(*args, **kwargs):
    from src.canalizaciones.canalizacion_facial import predecir_asistencia as ejecutar
    return ejecutar(*args, **kwargs)


def obtener_embeddings_faciales(*args, **kwargs):
    from src.canalizaciones.canalizacion_facial import obtener_embeddings_faciales as ejecutar
    return ejecutar(*args, **kwargs)


def invalidar_modelo_facial():
    modulo = sys.modules.get('src.canalizaciones.canalizacion_facial')
    if modulo is not None: modulo.invalidar_modelo_facial()


def obtener_embedding_voz(*args, **kwargs):
    from src.canalizaciones.canalizacion_voz import obtener_embedding_voz as ejecutar
    return ejecutar(*args, **kwargs)


def procesar_audio_masivo(*args, **kwargs):
    from src.canalizaciones.canalizacion_voz import procesar_audio_masivo as ejecutar
    return ejecutar(*args, **kwargs)
