"""Rutas públicas y portales: la ruta elegida nunca determina la identidad."""
import streamlit as st
from src.componentes.pie_pagina import pie_pagina_global


def navegar(renderizar_portal):
    def vista(rol, *, perfil=False, configuracion=False):
        def mostrar():
            st.session_state['tipo_sesion'] = rol
            st.session_state['_vista_estudiante'] = 'perfil' if perfil else 'portal'
            st.session_state['_vista_profesor'] = 'configuracion' if configuracion else 'perfil' if perfil else 'portal'
            renderizar_portal()
        return mostrar
    inicio = st.Page(vista(None), title='UPC | Aula', default=True)
    alias = st.Page(vista(None), title='Inicio', url_path='inicio')
    portales = {
        'profesor': st.Page(vista('profesor'), title='Portal docente', url_path='docente'),
        'estudiante': st.Page(vista('estudiante'), title='Portal estudiantil', url_path='estudiante'),
        'administrador': st.Page(vista('administrador'), title='Gestión académica', url_path='administracion'),
    }
    perfil = st.Page(vista('estudiante', perfil=True), title='Mi perfil', url_path='mi-perfil')
    perfil_docente = st.Page(vista('profesor', perfil=True), title='Mi perfil docente', url_path='mi-perfil-docente')
    configuracion_docente = st.Page(vista('profesor', configuracion=True), title='Configuración docente', url_path='configuracion-docente')
    pagina = st.navigation([inicio, alias, *portales.values(), perfil, perfil_docente, configuracion_docente], position='hidden')
    st.session_state['_pagina_inicio'] = inicio
    st.session_state['_paginas_portal'] = portales
    st.session_state['_pagina_perfil_estudiante'] = perfil
    st.session_state['_pagina_perfil_profesor'] = perfil_docente
    st.session_state['_pagina_configuracion_profesor'] = configuracion_docente
    with pie_pagina_global():
        pagina.run()


def abrir_perfil_estudiante():
    from src.utilidades.sesiones import obtener_actor
    actor = obtener_actor(renovar=True)
    if actor is None or actor[0] != 'estudiante':
        raise PermissionError('Este perfil requiere una sesión válida de estudiante.')
    st.switch_page(st.session_state['_pagina_perfil_estudiante'])


def abrir_perfil():
    from src.utilidades.sesiones import obtener_actor
    actor = obtener_actor(renovar=True)
    if actor is None or actor[0] not in ('profesor', 'estudiante'):
        raise PermissionError('El perfil requiere una sesión académica válida.')
    st.switch_page(st.session_state['_pagina_perfil_' + actor[0]])


def abrir_configuracion_docente():
    from src.utilidades.sesiones import obtener_actor
    actor = obtener_actor(renovar=True)
    if actor is None or actor[0] != 'profesor':
        raise PermissionError('La configuración requiere una sesión docente válida.')
    st.switch_page(st.session_state['_pagina_configuracion_profesor'])


@st.fragment(run_every='30s')
def vigilar_sesion():
    from src.utilidades.sesiones import obtener_actor
    import oracledb
    try:
        if obtener_actor(renovar=False) is None:
            st.rerun(scope='app')
    except oracledb.Error:
        st.warning('No se pudo comprobar la sesión. Las operaciones requieren validación del servidor.')
