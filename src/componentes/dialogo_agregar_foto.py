import streamlit as st
import time 
import numpy as np

from PIL import Image 



@st.dialog("Capturar o Subir Fotos")
def dialogo_agregar_foto():
    st.write("Agrega fotos del salón de clases para escanear la asistencia")

    if "pestana_foto" not in st.session_state:
        st.session_state.pestana_foto = "camara"
    if "claves_subidas_procesadas" not in st.session_state:
        st.session_state.claves_subidas_procesadas = set()
    if "clave_camara_procesada" not in st.session_state:
        st.session_state.clave_camara_procesada = None

    t1, t2 = st.columns(2)

    with t1:
        tipo_camara = "primary" if st.session_state.pestana_foto == "camara" else "tertiary"
        if st.button("Cámara", type=tipo_camara, width="stretch"):
            st.session_state.pestana_foto = "camara"
            
    with t2:
        tipo_subir = "primary" if st.session_state.pestana_foto == "subir" else "tertiary"
        if st.button("Subir Fotos", type=tipo_subir, width="stretch"):
            st.session_state.pestana_foto = "subir"

    if st.session_state.pestana_foto == "camara":
        foto_camara = st.camera_input("Tomar Foto", key="dialog_cam")
        if foto_camara:
            clave_camara = f"{foto_camara.name}_{foto_camara.size}"
            if st.session_state.clave_camara_procesada != clave_camara:
                st.session_state.imagenes_asistencia.append(Image.open(foto_camara))
                st.session_state.clave_camara_procesada = clave_camara
                st.toast("Foto capturada")
                time.sleep(1)

    if st.session_state.pestana_foto == "subir":
        archivos_subidos = st.file_uploader("elige archivos de imagen", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="dialog_upload")

        if archivos_subidos: 
            for archivo in archivos_subidos:
                clave_archivo = f"{archivo.name}_{archivo.size}"
                if clave_archivo not in st.session_state.claves_subidas_procesadas:
                    st.session_state.imagenes_asistencia.append(Image.open(archivo))
                    st.session_state.claves_subidas_procesadas.add(clave_archivo)
                    st.toast("Foto subida exitosamente")
                    time.sleep(1)

    st.divider() 

    if st.button("Listo", type="secondary", width="stretch"):
        st.rerun()
