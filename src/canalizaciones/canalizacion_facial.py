import dlib
import numpy as np
import face_recognition_models
from sklearn.svm import SVC
import streamlit as st

from src.base_datos.bd import obtener_todos_estudiantes


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


def obtener_embeddings_faciales(imagen_np):
    detector, sp, facerec = cargar_modelos_dlib()
    rostros = detector(imagen_np, 1) # 2

    codificaciones = []

    for rostro in rostros:
        forma = sp(imagen_np, rostro)
        descriptor_rostro = facerec.compute_face_descriptor(imagen_np, forma, 1)

        codificaciones.append(np.array(descriptor_rostro))

    return codificaciones


@st.cache_resource
def obtener_modelo_entrenado():
    X = []
    y = []

    estudiantes_bd = obtener_todos_estudiantes()

    if not estudiantes_bd:
        return None

    for estudiante in estudiantes_bd:
        embedding = estudiante.get('embedding_facial')
        if embedding:
            X.append(np.array(embedding))
            y.append(estudiante.get('estudiante_id'))

    if len(X) == 0:
        return None

    clf = SVC(kernel="linear", probability=True, class_weight="balanced")

    try:
        clf.fit(X, y)

    except ValueError:
        pass

    return {"clf":clf, "X":X, "y":y}


def entrenar_clasificador():
    st.cache_resource.clear()
    datos_modelo =  obtener_modelo_entrenado()
    return bool(datos_modelo)

def predecir_asistencia(imagen_clase_np):
    codificaciones = obtener_embeddings_faciales(imagen_clase_np)

    estudiante_detectado = {}

    datos_modelo = obtener_modelo_entrenado()

    # retorna: i> estudiantes coincidentes (ids predichos), ii> lista de todos los ids de estudiantes en la BD, iii> total de rostros detectados en la imagen (total de codificaciones)
    if not datos_modelo:
        return estudiante_detectado, [], len(codificaciones)

    clf = datos_modelo["clf"]
    X_entrenamiento = datos_modelo["X"]
    y_entrenamiento = datos_modelo["y"]

    # ids de estudiantes en la base de datos
    todos_estudiantes = sorted(list(set(y_entrenamiento)))

    # codificaciones en tiempo real
    for codificacion in codificaciones:
        if len(todos_estudiantes) >= 2:   
            id_predicho = int(clf.predict([codificacion])[0])
            # obtiene los puntajes de confianza del clasificador
            probabilidades = clf.predict_proba([codificacion])[0]
            confianza = np.max(probabilidades)
        else: # len = 1, ya que len = 0 se maneja en obtener_modelo_entrenado
            id_predicho = int(todos_estudiantes[0])
            confianza = 1.0

        # obtiene el embedding exacto para validación adicional
        embedding_estudiante = X_entrenamiento[y_entrenamiento.index(id_predicho)]

        # numpy linalg permite operar sobre embeddings (vectores) o listas/arreglos convertidos a np.array()
        mejor_puntaje_coincidencia = np.linalg.norm(embedding_estudiante - codificacion)

        # Validación balanceada: prioriza precisión en coincidencias reales mientras filtra falsos positivos claros
        umbral_semejanza = 0.55
        confianza_minima = 0.60

        if mejor_puntaje_coincidencia <= umbral_semejanza and confianza >= confianza_minima:
            estudiante_detectado[id_predicho] = True
        elif mejor_puntaje_coincidencia <= 0.50 and len(todos_estudiantes) >= 2:
            # Una coincidencia muy fuerte (distancia <= 0.50) debe aceptarse incluso con confianza moderada
            if len(todos_estudiantes) >= 2:
                # Verifica que sea claramente la mejor coincidencia
                distancias = []
                for id_estudiante in todos_estudiantes:
                    emb_estudiante = X_entrenamiento[y_entrenamiento.index(id_estudiante)]
                    dist = np.linalg.norm(emb_estudiante - codificacion)
                    distancias.append((id_estudiante, dist))
                
                distancias.sort(key=lambda x: x[1])
                
                if distancias[0][0] == id_predicho:
                    estudiante_detectado[id_predicho] = True
            else:
                estudiante_detectado[id_predicho] = True

    # retorna: i> diccionario de ids de estudiantes detectados, ii> lista de todos los ids de estudiantes de la BD, iii> total de rostros en la imagen (longitud del arreglo de codificaciones)
    return estudiante_detectado, todos_estudiantes, len(codificaciones)
