import streamlit as st
from src.componentes.encabezado import encabezado_inicio
from src.componentes.pie_pagina import pie_pagina_inicio
from src.utilidades.sesiones import seleccionar_portal


def pantalla_inicio():
    encabezado_inicio()
    st.html('<section class="upc-hero" aria-labelledby="upc-presentacion">'
            '<div class="upc-hero-content"><div class="upc-eyebrow">UNIVERSIDAD POPULAR DEL CESAR</div>'
            '<h1 id="upc-presentacion">Gestión y seguimiento académico.</h1>'
            '<p class="upc-hero-description">Consulta de asignaturas, registro de sesiones y seguimiento de la actividad académica.</p></div>'
            '<aside class="upc-hero-identity" aria-label="Lema institucional">'
            '<p class="upc-motto">Educación y Futuro</p></aside></section>'
            '<div class="upc-section-label">Acceso a los portales</div>')
    estudiante, profesor = st.columns(2, gap='large')
    with estudiante, st.container(key='portal_estudiante'):
        st.html('<div class="upc-role"><h2>Estudiantes</h2>'
                '<p>Inscripción en asignaturas y consulta de registros personales.</p></div>')
        st.button('Portal del Estudiante', type='secondary', width='content', icon=':material/arrow_forward:',
                  icon_position='right', on_click=seleccionar_portal, args=('estudiante',))
    with profesor, st.container(key='portal_profesor'):
        st.html('<div class="upc-role"><h2>Docentes</h2>'
                '<p>Gestión de asignaturas, sesiones y registros de asistencia.</p></div>')
        st.button('Portal del Profesor', type='secondary', width='content', icon=':material/arrow_forward:',
                  icon_position='right', on_click=seleccionar_portal, args=('profesor',))
    pie_pagina_inicio()
