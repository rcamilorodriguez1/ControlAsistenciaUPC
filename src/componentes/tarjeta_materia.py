from html import escape
import streamlit as st


def tarjeta_materia(nombre, codigo, seccion, estadisticas=None, al_pie=None):
    partes = ['<article class="upc-course"><div class="upc-course-top"><h3>', escape(str(nombre)),
              '</h3><span class="upc-course-code">', escape(str(codigo)), '</span></div>',
              '<p class="upc-course-section">Sección ', escape(str(seccion or 'Sin sección')), '</p>']
    if estadisticas:
        partes.append('<div class="upc-course-stats">')
        for _, etiqueta, valor in estadisticas:
            partes.append('<span><strong>' + escape(str(valor)) + '</strong> ' + escape(str(etiqueta)) + '</span>')
        partes.append('</div>')
    partes.append('</article>')
    st.html(''.join(partes))
    if al_pie: al_pie()
