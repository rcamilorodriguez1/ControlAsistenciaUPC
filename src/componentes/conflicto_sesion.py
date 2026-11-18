"""Aviso compartido debajo de los formularios, sin sustituirlos."""
import streamlit as st
from src.utilidades.sesiones import sesion_incompatible, volver_a_mi_portal, salir_al_portal


def mostrar_conflicto_sesion(portal):
    actor = sesion_incompatible(portal)
    if actor is None:
        return
    nombres = {'profesor': 'docente', 'estudiante': 'estudiantil', 'administrador': 'administrativo'}
    with st.container(key='aviso_conflicto_sesion', border=True):
        with st.container(horizontal=True, vertical_alignment='center', gap='small'):
            st.markdown(':material/info:', width='content')
            st.subheader('Ya tienes una sesión activa', anchor=False)
        st.write(f'Actualmente tienes una sesión iniciada en el portal {nombres[actor[0]]}. '
                 'Para acceder a este portal, primero debes cerrar tu sesión actual.')
        volver, cerrar = st.columns(2)
        with volver:
            st.button('Volver a mi portal', type='primary', on_click=volver_a_mi_portal)
        with cerrar:
            st.button('Cerrar sesión actual', on_click=salir_al_portal, args=(portal,))
