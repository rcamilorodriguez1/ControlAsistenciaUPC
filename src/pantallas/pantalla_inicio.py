import streamlit as st
from src.componentes.encabezado import encabezado_inicio
from src.interfaz.diseno_base import estilo_diseno_base, estilo_fondo_inicio
from src.componentes.pie_pagina import pie_pagina_inicio 

def pantalla_inicio():

    encabezado_inicio()

    estilo_fondo_inicio()
    estilo_diseno_base()

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.header("Soy Estudiante")
        st.image("https://i.ibb.co/844D9Lrt/mascot-student.png", width=120)
        if st.button("Portal del Estudiante", icon=':material/arrow_outward:', icon_position="right"):
            st.session_state["tipo_sesion"]="estudiante"
            st.rerun()

    with col2:
        st.header("Soy Profesor")
        st.image("https://i.ibb.co/CsmQQV6X/mascot-prof.png", width=150 )
        if st.button("Portal del Profesor", type="primary", icon=":material/arrow_outward:", icon_position="right"):
            st.session_state["tipo_sesion"]="profesor"
            st.rerun()

    pie_pagina_inicio()
