import io
from urllib.parse import urlsplit
import segno
import streamlit as st
from src.utilidades.enlaces import crear_enlace_union


@st.dialog('Compartir materia', width='large')
def dialogo_compartir_materia(nombre_materia, codigo_materia):
    try:
        url_union = crear_enlace_union(codigo_materia)
    except ValueError as exc:
        st.error(f'No se pudo crear el enlace de inscripción: {exc}')
        return
    st.subheader(nombre_materia)
    st.caption('Comparte el enlace o el código con tus estudiantes para que se inscriban.')
    qr = segno.make(url_union)
    salida = io.BytesIO()
    qr.save(salida, kind='png', scale=8, border=4)
    enlace, imagen = st.columns([3, 2], gap='large')
    with enlace:
        st.markdown('**Enlace de inscripción**')
        st.code(url_union, language='text', wrap_lines=True)
        st.markdown('**Código de la materia**')
        st.code(codigo_materia, language='text')
        if urlsplit(url_union).hostname in ('localhost', '127.0.0.1', '::1'):
            st.info('Este enlace es local: se abre en el mismo equipo que ejecuta la aplicación.')
    with imagen:
        st.image(salida.getvalue(), width=240, caption='Escanea para abrir la inscripción')
