import streamlit as st

from src.componentes.pie_pagina import pie_pagina_panel
from src.componentes.encabezado import encabezado_panel
from src.componentes.dialogo_inscripcion import dialogo_inscripcion
from src.componentes.tarjeta_materia import tarjeta_materia

from src.interfaz.diseno_base import (
    estilo_fondo_panel,
    estilo_diseno_base,
    estilo_espaciado_compacto,
)

import numpy as np
import time
from PIL import Image

from src.base_datos.bd import obtener_todos_estudiantes, crear_estudiante, obtener_materias_estudiante, obtener_asistencia_estudiante, desmatricular_estudiante_de_materia, obtener_resumen_estudiante

from src.canalizaciones.canalizacion_facial import predecir_asistencia, obtener_embeddings_faciales, entrenar_clasificador
from src.canalizaciones.canalizacion_voz import obtener_embedding_voz

def panel_estudiante():
    datos_estudiante = st.session_state.datos_estudiante
    id_estudiante = datos_estudiante["estudiante_id"]

    logo_url= "https://i.ibb.co/YTYGn5qV/logo.png"  

    logo_col, spacer_col, action_col = st.columns([1.2, 2.2, 2.2], vertical_alignment="center")

    with logo_col:
        st.markdown(
            f"""
            <div style="display:flex; justify-content:flex-start;">
                <img src="{logo_url}" style="height:100px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )

    with action_col:
        if st.button( "Cerrar sesión",  type="primary",  key="loginbackbtn", shortcut="Ctrl+Backspace", width="stretch"):
            st.session_state["sesion_iniciada"] = False
            del st.session_state.datos_estudiante
            st.rerun()

    st.markdown(
        """
        <h1 style="text-align:center; color:#1B2E10; margin-bottom:30px;">Control De Asistencia UPC</h1>
        """,
        unsafe_allow_html=True,
    )

    st.header(f"""Bienvenido, {datos_estudiante['nombre']} """)

    resumen = obtener_resumen_estudiante(id_estudiante)

    with st.container(border=True):
        k1, k2, k3 = st.columns(3)
        k1.metric("Materias Inscritas", resumen["total_materias"])
        k2.metric("Clases Registradas", resumen["total_clases"])
        k3.metric("Asistencia Promedio", f"{resumen['asistencia_promedio']:.0f}%")

    st.space() 

    c1, c2 = st.columns(2)
    with c1:
        st.header("Tus Materias Inscritas")
    with c2:
        st.space()
        if st.button("Inscribirse en una Materia", type="primary", width="stretch"):
            dialogo_inscripcion()

    st.divider()

    with st.spinner("Cargando tus materias inscritas..."):
        materias = obtener_materias_estudiante(id_estudiante)
        registros = obtener_asistencia_estudiante(id_estudiante)

        mapa_estadisticas = {}

        for registro in registros:
            id_materia = registro["materia_id"]
            if id_materia not in mapa_estadisticas:
                mapa_estadisticas[id_materia] = {"total":0, "asistio":0}

            mapa_estadisticas[id_materia]["total"] += 1

            if registro.get("presente"):
                mapa_estadisticas[id_materia]["asistio"] += 1

        columnas = st.columns(2)    
        for i, nodo_materia in enumerate(materias):
            materia = nodo_materia["materia"]
            id_materia = materia["materia_id"]

            estadisticas = mapa_estadisticas.get(id_materia, {"total": 0, "asistio": 0})

            def boton_retirar():
                if st.button("Retirarse de esta materia", type="tertiary", width="stretch", icon=":material/delete_forever:", key=f"unenroll_{id_materia}"):
                    desmatricular_estudiante_de_materia(id_estudiante, id_materia)
                    st.toast(f"Te has retirado de {materia['nombre']} exitosamente")
                    time.sleep(1)
                    st.rerun()

            with columnas[i%2]:
                tarjeta_materia(
                    nombre=materia["nombre"],
                    codigo=materia["codigo_materia"],
                    seccion=materia["seccion"],
                    estadisticas=[
                        ("🗓️", "Total", estadisticas["total"]),
                        ("☑️", "Asistió", estadisticas["asistio"]),
                    ],
                    al_pie=boton_retirar  
                )

    pie_pagina_panel()


def pantalla_estudiante():

    estilo_fondo_panel()
    estilo_diseno_base()
    estilo_espaciado_compacto()

    if "datos_estudiante" in st.session_state:
        panel_estudiante()
        return

    if "mostrar_registro_estudiante" not in st.session_state:
        st.session_state.mostrar_registro_estudiante = False

    encabezado_panel()

    st.markdown(
        """
        <style>

            [data-testid="stAppViewContainer"] .block-container {
                padding-top: 10px !important;
                margin-top: -50px !important;
            }
        
            div[data-testid="stHeadingWithActionElements"] {
                margin-top: -1rem !important;
                margin-bottom: -0.45rem !important;
            }

            div[data-testid="stHeadingWithActionElements"] + div[data-testid="stWidgetLabel"] {
                margin-top: -0.4rem !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.header("Inicia sesión con tu Rostro", text_alignment="center")

    fuente_foto = st.camera_input("Ubica tu rostro en el centro")
    if not fuente_foto:
        st.session_state.mostrar_registro_estudiante = False

    if fuente_foto and not st.session_state.mostrar_registro_estudiante:
        imagen = np.array(Image.open(fuente_foto))

        with st.spinner("La IA está escaneando..."):
            detectado, todos_ids, num_rostros = predecir_asistencia(imagen)

            if num_rostros == 0:
                st.warning("¡No se encontró ningún rostro en la imagen!")
            elif num_rostros>1:
                st.warning("Se encontraron múltiples rostros en la imagen")
            else:

                if detectado:
                    id_estudiante = list(detectado.keys())[0]
                    todos_estudiantes = obtener_todos_estudiantes()
                    estudiante = next((e for e in todos_estudiantes if e["estudiante_id"]==id_estudiante), None)

                    if estudiante:
                        st.session_state.sesion_iniciada = True 
                        st.session_state.rol_usuario = "estudiante"
                        st.session_state.datos_estudiante = estudiante
                        st.toast(f"{estudiante['nombre']} - ¡Bienvenido de nuevo!")
                        time.sleep(1)
                        st.rerun()


                else:    
                    st.info("¡Rostro no reconocido! Puede que seas un nuevo estudiante")
                    st.session_state.mostrar_registro_estudiante = True

    if st.session_state.mostrar_registro_estudiante and fuente_foto:
        with st.container(border=True):
            st.header("Registrar nuevo perfil")
            nuevo_nombre = st.text_input("Ingresa tu nombre", placeholder=" Ej. Mihir Gupta")

            st.subheader("(Opcional): Inscripción de voz")
            st.info("Inscribe tu voz para el registro de asistencia")

            audio_grabado = None

            try:
                audio_grabado = st.audio_input(
                    f"Graba una frase corta para capturar tu voz. Ejemplo: 'Estoy presente profesor, mi nombre es {nuevo_nombre}'"
                )
            except Exception:
                st.error("Ocurrió un error al capturar la voz para la grabación")

            if st.button("Crear Cuenta", type="primary"):
                if nuevo_nombre:
                    with st.spinner("Creando perfil..."):
                        imagen = np.array(Image.open(fuente_foto))
                        codificaciones = obtener_embeddings_faciales(imagen)
                        if codificaciones:
                            emb_facial = codificaciones[0].tolist()

                            emb_voz = None
                            if audio_grabado:
                                audio_bytes = audio_grabado.getvalue()
                                if audio_bytes:
                                    emb_voz = obtener_embedding_voz(audio_bytes)

                            datos_respuesta = crear_estudiante(
                                nuevo_nombre,
                                embedding_facial=emb_facial,
                                embedding_voz=emb_voz,
                            )

                            if datos_respuesta:
                                entrenar_clasificador()

                                st.session_state.sesion_iniciada = True
                                st.session_state.rol_usuario = "estudiante"
                                st.session_state.datos_estudiante = datos_respuesta[0]
                                st.session_state.mostrar_registro_estudiante = False
                                st.toast(f"Bienvenido {nuevo_nombre} \n Perfil creado exitosamente")
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error("¡Ocurrió un error al capturar los rasgos faciales para el registro!")
                else:
                    st.warning("¡Por favor ingresa tu nombre!")




    pie_pagina_panel()
