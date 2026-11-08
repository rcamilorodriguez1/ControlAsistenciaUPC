import streamlit as st
from src.pantallas.pantalla_inicio import pantalla_inicio
from src.pantallas.pantalla_estudiante import pantalla_estudiante
from src.pantallas.pantalla_profesor import pantalla_profesor

from src.componentes.dialogo_inscripcion_automatica import dialogo_inscripcion_automatica

def principal():

    st.set_page_config(
        page_title="Control De Asistencia UPC",
        page_icon="https://i.ibb.co/YTYGn5qV/logo.png",
    )

    if "tipo_sesion" not in st.session_state:
        st.session_state["tipo_sesion"] = None

    match st.session_state["tipo_sesion"]:
        case "profesor":
            pantalla_profesor()

        case "estudiante":
            pantalla_estudiante()

        case None:
            pantalla_inicio()

    codigo_union = st.query_params.get("join-code")
    if codigo_union:
        if st.session_state.tipo_sesion != "estudiante":
            st.session_state.tipo_sesion = "estudiante"
            st.rerun()

        if st.session_state.get("sesion_iniciada") and st.session_state.get("rol_usuario") == "estudiante":
            dialogo_inscripcion_automatica(codigo_union)


principal()
