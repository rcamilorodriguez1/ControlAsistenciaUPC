import streamlit as st

from src.utilidades.imagenes import agregar_foto
from src.utilidades.sesiones import contexto_vigente


def _seleccionar_fuente(fuente):
    st.session_state.pestana_foto = fuente


@st.dialog("Capturar o Subir Fotos")
def dialogo_agregar_foto(contexto):
    if not contexto_vigente(contexto):
        st.warning("La sesión o materia cambió. Cierra este diálogo y abre una nueva captura.")
        return
    st.write("Agrega fotos del salón de clases para escanear la asistencia")
    st.caption("Hasta 12 fotos JPEG/PNG: 10 MB y 20 megapíxeles por foto; 60 MB en total.")
    fuente = st.session_state.setdefault("pestana_foto", "camara")
    t1, t2 = st.columns(2)
    with t1:
        st.button("Cámara", type="primary" if fuente == "camara" else "tertiary", width="stretch",
                  on_click=_seleccionar_fuente, args=("camara",))
    with t2:
        st.button("Subir Fotos", type="primary" if fuente == "subir" else "tertiary", width="stretch",
                  on_click=_seleccionar_fuente, args=("subir",))
    toma_id = contexto["toma_id"]
    if fuente == "camara":
        foto = st.camera_input("Tomar Foto", key=f"captura_camara_{toma_id}")
        archivos = [foto] if foto else []
    else:
        archivos = st.file_uploader("Elige archivos de imagen", type=["jpg", "png", "jpeg"],
                                    accept_multiple_files=True, key=f"captura_archivos_{toma_id}") or []
    for archivo in archivos:
        try:
            if agregar_foto(archivo, contexto):
                st.toast("Foto agregada")
        except (ValueError, PermissionError) as exc:
            st.warning(str(exc))
    st.divider()
    if st.button("Listo", type="secondary", width="stretch"):
        st.rerun()
