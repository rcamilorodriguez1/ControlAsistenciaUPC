import dlib
import numpy as np
import face_recognition_models
import streamlit as st

from src.base_datos.bd import obtener_todos_estudiantes
from src.utilidades.biometria import MuestraInvalida, validar_vector_facial
from src.utilidades.muestra_facial import validar_imagen_rgb, MIN_LADO_ROSTRO
from src.servicios.identificacion import ClasificadorReferencias


@st.cache_resource  
def cargar_modelos_dlib():
    detector = dlib.get_frontal_face_detector()

    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec


def obtener_embeddings_faciales(imagen_np, *, rostro_unico=False):
    imagen_np = validar_imagen_rgb(imagen_np)
    detector, sp, facerec = cargar_modelos_dlib()
    rostros = detector(imagen_np, 1) # 2
    if rostro_unico:
        if len(rostros) != 1:
            raise MuestraInvalida('Para registrar el perfil debe aparecer exactamente un rostro.', 'ROSTRO_UNICO')
        rostro = rostros[0]
        alto, ancho = imagen_np.shape[:2]
        if (min(rostro.width(), rostro.height()) < MIN_LADO_ROSTRO or rostro.left() < 0 or rostro.top() < 0
                or rostro.right() >= ancho or rostro.bottom() >= alto):
            raise MuestraInvalida('Acerca el rostro y mantenlo completo dentro de la imagen.', 'CALIDAD_ROSTRO')

    codificaciones = []

    for rostro in rostros:
        forma = sp(imagen_np, rostro)
        descriptor_rostro = facerec.compute_face_descriptor(imagen_np, forma, 1)

        codificaciones.append(validar_vector_facial(descriptor_rostro))

    return codificaciones


@st.cache_resource
def obtener_modelo_entrenado():
    referencias = {}
    for estudiante in obtener_todos_estudiantes():
        embedding = estudiante.get('embedding_facial')
        if embedding is not None:
            sid = estudiante['estudiante_id']
            if sid in referencias:
                raise ValueError('Hay referencias duplicadas para una identidad.')
            referencias[sid] = embedding
    return ClasificadorReferencias(referencias)


def entrenar_clasificador():
    invalidar_modelo_facial()
    datos_modelo =  obtener_modelo_entrenado()
    return bool(datos_modelo.referencias)


def invalidar_modelo_facial():
    obtener_modelo_entrenado.clear()

def predecir_asistencia(imagen_clase_np, *, rostro_unico=False, permitidos=None):
    codificaciones = obtener_embeddings_faciales(imagen_clase_np, rostro_unico=rostro_unico)

    modelo = obtener_modelo_entrenado()
    permitidos = None if permitidos is None else set(permitidos)
    ids = sorted(sid for sid in modelo.referencias if permitidos is None or sid in permitidos)
    detectados = {}
    for codificacion in codificaciones:
        resultado = modelo.identificar(codificacion, permitidos=permitidos)
        if resultado.identidad is not None:
            detectados[resultado.identidad] = True
    return detectados, ids, len(codificaciones)
