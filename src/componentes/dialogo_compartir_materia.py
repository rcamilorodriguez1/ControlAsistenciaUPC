import streamlit as st
import segno
import io
from urllib.parse import quote

from src.base_datos.configuracion import URL_APP

@st.dialog("Compartir Enlace de la Clase")
def dialogo_compartir_materia(nombre_materia, codigo_materia):
    url_union = f"{URL_APP}/?join-code={quote(str(codigo_materia))}"

    st.header("Escanear para Unirse")

    qr = segno.make(url_union)
    salida = io.BytesIO()
    qr.save(salida, kind="png", scale=10, border=1) 

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Copiar Enlace")
        st.code(url_union, language="text")
        st.code(codigo_materia, language="text")
        st.info("Copia este enlace para compartirlo por WhatsApp o correo electrónico")

    with col2:
        st.markdown("### Escanear para Unirse")
        st.image(salida.getvalue(), caption="Código QR para unirse a la clase")
