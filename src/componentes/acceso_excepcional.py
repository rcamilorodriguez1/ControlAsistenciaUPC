"""Alternativa accesible sin cámara, aislada de los errores de captura facial."""
import logging
import streamlit as st
from src.servicios.verificacion_identidad import autenticar_excepcion, autenticar_prueba_academica, TIPOS_DOCUMENTO
from src.servicios.clave_maestra_pruebas import configuracion_pruebas
from src.utilidades.sesiones import iniciar_sesion

_logger = logging.getLogger(__name__)


def acceso_excepcional(*, deshabilitado=False):
    token = st.session_state.sesion_token
    with st.expander('No puedo completar la validación biométrica'):
        st.caption('Usa tu documento y la clave que te entregue tu docente o Gestión académica. Si aún no tienes autorización, solicítala a tu docente.')
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
        if configuracion_pruebas() is not None:
            st.markdown('**Demostración académica**')
            st.caption('Acceso temporal para estudiantes activos: utiliza tu documento registrado y la clave común de la presentación. Si falta el documento, complétalo en tu perfil o solicita ayuda a Gestión académica.')
            with st.form('acceso_academico_prueba'):
                tipo_prueba = st.selectbox('Tipo de documento de la prueba', TIPOS_DOCUMENTO,
                                           disabled=deshabilitado, key=f'auth_estudiante_tipo_prueba_{token}')
                numero_prueba = st.text_input('Número de documento registrado', max_chars=40, disabled=deshabilitado,
                                              key=f'auth_estudiante_documento_prueba_{token}')
                maestra = st.text_input('Clave de prueba académica', type='password', disabled=deshabilitado,
                                        key=f'auth_estudiante_maestra_prueba_{token}')
                probar = st.form_submit_button('Ingresar para la demostración', disabled=deshabilitado)
            if probar:
                try:
                    perfil = autenticar_prueba_academica(tipo_prueba, numero_prueba, maestra)
                    if perfil:
                        iniciar_sesion('estudiante', perfil)
                    else:
                        st.error('No se pudo validar el acceso de prueba. Revisa el documento, la clave y la vigencia; tras varios fallos espera 15 minutos.')
                except (ValueError, PermissionError) as exc:
                    st.warning(str(exc))
                except Exception as exc:
                    _logger.error('Fallo de acceso académico: tipo=%s', type(exc).__name__)
                    st.error('No se pudo completar el acceso de prueba. Intenta de nuevo.')
                else:
                    if perfil:
                        st.rerun()
