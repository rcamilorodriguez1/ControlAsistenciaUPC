import streamlit as st
from src.base_datos.bd import matricular_estudiante_en_materia, obtener_materia_por_codigo, esta_estudiante_matriculado
import oracledb
from src.utilidades.sesiones import misma_sesion, limpiar_codigo_union

@st.dialog("Inscripción Rápida", on_dismiss=limpiar_codigo_union)
def dialogo_inscripcion_automatica(codigo_materia, token):
    if (not misma_sesion("estudiante", token)
            or st.query_params.get("join-code", "").strip() != codigo_materia):
        st.warning("Esta invitación ya no pertenece a la sesión actual.")
        return
    id_estudiante = st.session_state.datos_estudiante["estudiante_id"]

    materia = obtener_materia_por_codigo(codigo_materia)
    if not materia:
        st.error(f"¡Materia {codigo_materia} no encontrada!")
        if st.button("Cerrar"):
            limpiar_codigo_union()
            st.rerun()
        return

    if esta_estudiante_matriculado(materia["materia_id"], id_estudiante):
        st.info("¡Ya estás inscrito!")
        if st.button("¡Entendido!", type="primary"):
            limpiar_codigo_union()
            st.rerun()
        return

    
    st.markdown(f"¿Te gustaría inscribirte en **{materia['nombre']}**?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("¡No, gracias!"):
            limpiar_codigo_union()
            st.rerun()
    
    with col2:
        if st.button("¡Sí, inscribirme ahora!", type="primary", width="stretch"):
            try:
                matricular_estudiante_en_materia(id_estudiante, materia["materia_id"])
            except oracledb.IntegrityError as exc:
                if exc.args[0].code != 1:
                    raise
                limpiar_codigo_union()
                st.rerun()
            st.success(f"Te has inscrito exitosamente en {materia['nombre']}")
            limpiar_codigo_union()
            st.rerun()
