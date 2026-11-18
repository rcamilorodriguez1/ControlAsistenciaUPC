import streamlit as st
from html import escape
from contextlib import contextmanager
from contextvars import ContextVar
from src.interfaz.creditos_academicos import CREDITOS_ACADEMICOS

_DIFERIR_PIE = ContextVar('pie_academico_diferido', default=False)


def html_pie_academico(datos=None):
    datos = CREDITOS_ACADEMICOS if datos is None else datos
    estudiantes = ''.join(f'<li>{escape(str(nombre))}</li>' for nombre in datos['estudiantes'])
    asignatura = escape(str(datos['asignatura']).rstrip('.'))
    docente = escape(str(datos['docente']))
    programa = escape(str(datos['programa']))
    anio = escape(str(datos['anio']))
    return (
        '<footer class="upc-academic-footer" aria-label="Créditos del proyecto académico">'
        '<div class="academic-footer-main">'
        '<section class="academic-footer-zone academic-footer-students" aria-labelledby="academic-students-title">'
        '<div class="academic-footer-heading"><p class="academic-footer-label">01 — Desarrolladores</p>'
        '<h2 class="academic-footer-title" id="academic-students-title">Estudiantes.</h2></div>'
        f'<ul class="academic-footer-credits" aria-label="Estudiantes desarrolladores">{estudiantes}</ul>'
        '</section>'
        '<section class="academic-footer-zone academic-footer-subject" aria-labelledby="academic-subject-title">'
        '<div class="academic-footer-heading"><p class="academic-footer-label">02 — Referencia académica</p>'
        f'<h2 class="academic-footer-title" id="academic-subject-title">{asignatura}.</h2></div>'
        '<dl class="academic-footer-record"><div><dt>Docente</dt>'
        f'<dd>{docente}</dd></div><div><dt>Programa</dt><dd>{programa}</dd></div></dl>'
        '</section></div>'
        '<div class="academic-footer-band"><span>UPC | Aula</span>'
        f'<span>Proyecto académico · {anio}</span></div></footer>'
    )


def _mostrar_pie():
    with st.container(key='pie_academico', gap=None):
        st.html(html_pie_academico())


@contextmanager
def pie_pagina_global():
    """Un solo cierre al terminar la vista, incluidos avisos posteriores y retornos tempranos."""
    token = _DIFERIR_PIE.set(True)
    try:
        yield
        _mostrar_pie()
    finally:
        _DIFERIR_PIE.reset(token)


def pie_pagina_inicio():
    if not _DIFERIR_PIE.get():
        _mostrar_pie()


def pie_pagina_panel():
    pie_pagina_inicio()
