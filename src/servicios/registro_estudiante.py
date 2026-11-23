"""Valida la captura completa antes de crear una cuenta o descartar una voz enviada."""

from src.base_datos.bd import crear_estudiante
from src.servicios.biometria_diferida import obtener_embeddings_faciales, invalidar_modelo_facial, obtener_embedding_voz
from src.utilidades.biometria import MuestraInvalida, validar_vector_facial, normalizar_vector_voz
from src.utilidades.muestra_facial import leer_foto_registro
from src.servicios.verificacion_identidad import normalizar_documento


def registrar_estudiante(nombre, foto, audio_bytes=None, *, tipo_documento, documento):
    from src.servicios.autenticacion import exigir_acceso_disponible
    exigir_acceso_disponible()
    if not isinstance(nombre, str) or not nombre.strip():
        raise MuestraInvalida('Ingresa tu nombre antes de crear el perfil.')
    documento = normalizar_documento(tipo_documento, documento)
    imagen = leer_foto_registro(foto)
    descriptores = obtener_embeddings_faciales(imagen, rostro_unico=True)
    if len(descriptores) != 1:
        raise MuestraInvalida('El registro necesita exactamente un rostro.', 'ROSTRO_UNICO')
    facial = validar_vector_facial(descriptores[0]).tolist()
    voz = None
    if audio_bytes is not None:
        voz = normalizar_vector_voz(obtener_embedding_voz(audio_bytes)).tolist()
    respuesta = crear_estudiante(nombre.strip(), embedding_facial=facial, embedding_voz=voz,
                                tipo_documento=tipo_documento, documento=documento)
    # No entrenar despues del COMMIT: un fallo de entrenamiento no debe fingir un alta fallida.
    invalidar_modelo_facial()
    return respuesta
