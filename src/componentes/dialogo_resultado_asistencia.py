import streamlit as st
import time 

from src.base_datos.bd import crear_asistencia



def mostrar_resultado_asistencia(df, registros):
    st.write("Por favor revisa la asistencia antes de confirmar.")
    
    st.dataframe(df, hide_index=True, width="stretch")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Descartar", width="stretch", type="tertiary"):
            st.session_state.imagenes_asistencia = []
            st.session_state.resultados_asistencia_voz = None
            st.rerun()
    
    with col2:
        if st.button("Confirmar y Aprobar", width="stretch", type="primary"):
            try:
                crear_asistencia(registros)
                st.success("Asistencia aprobada exitosamente")
                st.session_state.imagenes_asistencia = []
                st.session_state.resultados_asistencia_voz = None
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Ocurrió un error al registrar la asistencia {e}")


@st.dialog("Reportes de Asistencia")
def dialogo_resultado_asistencia(df, registros):
    mostrar_resultado_asistencia(df, registros)
