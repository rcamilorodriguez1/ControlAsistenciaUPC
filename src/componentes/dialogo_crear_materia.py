import streamlit as st
from src.base_datos.bd import crear_materia

@st.dialog("Crear Nueva Materia")
def dialogo_crear_materia(id_profesor):
    st.write("Ingresa los detalles de la nueva materia")
    codigo_materia = st.text_input("Código de Materia", placeholder="Ej. CSE101")
    nombre_materia = st.text_input("Nombre de la Materia", placeholder="Ej. Introducción a la Computación")
    seccion_materia = st.text_input("Sección", placeholder="Ej. K23AM")

    if st.button("Crear Materia Ahora", type="primary", width="stretch"):
        if codigo_materia and nombre_materia and seccion_materia:
            try:
                crear_materia(codigo_materia, nombre_materia, seccion_materia, id_profesor)
                st.toast("¡Materia creada exitosamente!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

        else:
            st.warning("Por favor completa todos los campos")
