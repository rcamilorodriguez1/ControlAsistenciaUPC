"""Alternativa accesible sin cámara, aislada de los errores de captura facial."""
import logging
import streamlit as st
from src.servicios.verificacion_identidad import autenticar_excepcion, TIPOS_DOCUMENTO
from src.utilidades.sesiones import iniciar_sesion

_logger = logging.getLogger(__name__)


def acceso_excepcional(*, deshabilitado=False):
    token = st.session_state.sesion_token
    with st.expander('No puedo completar la validación biométrica'):
        st.caption('Acceso alternativo previamente autorizado por Gestión académica. Si aún no tienes autorización, contacta con el responsable institucional.')
        with st.form('acceso_excepcional'):
            tipo = st.selectbox('Tipo de documento', TIPOS_DOCUMENTO, disabled=deshabilitado, key=f'auth_estudiante_tipo_{token}')
            documento = st.text_input('Número de documento', max_chars=40, disabled=deshabilitado, key=f'auth_estudiante_documento_{token}')
            clave = st.text_input('Contraseña de acceso alternativo', type='password', disabled=deshabilitado, key=f'auth_estudiante_clave_{token}')
            ingresar = st.form_submit_button('Ingresar mediante excepción', disabled=deshabilitado)
        if ingresar:
            try:
                perfil = autenticar_excepcion(tipo, documento, clave)
                if perfil:
                    iniciar_sesion('estudiante', perfil)
                else:
                    st.error('No se pudo validar el acceso. Revisa las credenciales y la autorización; tras varios fallos espera 15 minutos.')
            except (ValueError, PermissionError) as exc:
                st.warning(str(exc))
            except Exception as exc:
                _logger.error('Fallo de acceso excepcional: tipo=%s', type(exc).__name__)
                st.error('No se pudo completar la verificación. Intenta de nuevo o contacta con Gestión académica.')
            else:
                if perfil:
                    st.rerun()
