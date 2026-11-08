import streamlit as st
from src.base_datos.bd import matricular_estudiante_en_materia, obtener_materia_por_codigo, esta_estudiante_matriculado
import time

@st.dialog("Inscribirse en una Materia")
def dialogo_inscripcion():
    st.write("Ingresa el código de materia proporcionado por tu profesor para inscribirte")
    codigo_ingresado = st.text_input("Código de Materia", placeholder="Ej. CSE101")

    if st.button("Inscribirme Ahora", type="primary", width="stretch"):
        if codigo_ingresado:
            materia = obtener_materia_por_codigo(codigo_ingresado)
            if materia:
                id_estudiante = st.session_state.datos_estudiante["estudiante_id"]
                nombre_estudiante = st.session_state.datos_estudiante["nombre"]

                if esta_estudiante_matriculado(materia["materia_id"], id_estudiante):
                    st.warning(f"{nombre_estudiante} ya está inscrito en la materia {materia['nombre']}")
                else:
                    matricular_estudiante_en_materia(id_estudiante, materia["materia_id"])
                    st.success(f"{nombre_estudiante} se inscribió exitosamente en la materia {materia['nombre']}")
                    time.sleep(1)
                    st.rerun()

        else:
            st.warning("Por favor ingresa un código de materia") 
