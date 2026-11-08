import streamlit as st
from src.base_datos.bd import matricular_estudiante_en_materia, obtener_materia_por_codigo, esta_estudiante_matriculado
import time

@st.dialog("Inscripción Rápida")
def dialogo_inscripcion_automatica(codigo_materia):
    id_estudiante = st.session_state.datos_estudiante["estudiante_id"]

    materia = obtener_materia_por_codigo(codigo_materia)
    if not materia:
        st.error(f"¡Materia {codigo_materia} no encontrada!")
        if st.button("Cerrar"):
            st.query_params.clear()
            st.rerun()
        return

    if esta_estudiante_matriculado(materia["materia_id"], id_estudiante):
        st.info("¡Ya estás inscrito!")
        if st.button("¡Entendido!", type="primary"):
            st.query_params.clear()
            st.rerun()
        return

    
    st.markdown(f"¿Te gustaría inscribirte en **{materia['nombre']}**?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("¡No, gracias!"):
            st.query_params.clear()
            st.rerun()
    
    with col2:
        if st.button("¡Sí, inscribirme ahora!", type="primary", width="stretch"):
            matricular_estudiante_en_materia(id_estudiante, materia["materia_id"])
            st.success(f"Te has inscrito exitosamente en {materia['nombre']}")
            st.query_params.clear() 
            time.sleep(1)
            st.rerun()
