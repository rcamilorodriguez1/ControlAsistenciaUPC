"""Completar/corregir el documento desde el perfil propio, sin exponerlo completo."""
import streamlit as st
from src.servicios import documentos_estudiantes as documentos
from src.servicios.verificacion_identidad import TIPOS_DOCUMENTO
from src.utilidades.sesiones import cerrar_sesion


def configurar_documento():
    datos = documentos.consultar_propio()
    with st.expander('Configuración de mi documento', expanded=not bool(datos['final'])):
        st.caption(documentos.etiqueta_documento(datos['tipo'],datos['final']))
        st.caption('Usa este documento para el acceso alternativo. Si lo cambias, se cerrará tu sesión y tendrás que renovar cualquier excepción anterior.')
        with st.form(f'documento_propio_{datos["version"]}',clear_on_submit=True):
            tipo = st.selectbox('Tipo de documento de mi perfil',TIPOS_DOCUMENTO,
                               index=TIPOS_DOCUMENTO.index(datos['tipo']) if datos['tipo'] in TIPOS_DOCUMENTO else 0)
            numero = st.text_input('Número de mi documento',max_chars=40)
            comprobar = st.checkbox('Confirmo que el documento corresponde a mi cuenta.')
            guardar = st.form_submit_button('Guardar mi documento',type='primary')
        if guardar:
            try:
                documentos.guardar_propio(tipo,numero,version=datos['version'],comprobado=comprobar)
            except (ValueError,PermissionError) as exc:
                st.warning(str(exc))
            else:
                cerrar_sesion('estudiante')
                st.session_state['aviso_sesion']='Documento guardado. Inicia sesión nuevamente; utiliza ese documento para el acceso alternativo.'
                st.rerun()
