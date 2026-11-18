"""Formulario de recuperacion docente; no inicia sesion ni conserva secretos tras el cambio."""
import logging
import streamlit as st
from src.componentes.encabezado import encabezado_panel
from src.componentes.pie_pagina import pie_pagina_panel
from src.componentes.seguridad_claves import mostrar_fortaleza,mostrar_coincidencia
from src.servicios.recuperacion_acceso import restablecer_profesor
from src.utilidades.sesiones import cambiar_formulario_profesor

_logger=logging.getLogger(__name__)


def recuperar_clave_profesor():
    encabezado_panel()
    token=st.session_state.sesion_token
    with st.container(key='recuperacion_docente'):
        st.caption('RECUPERACIÓN DE ACCESO DOCENTE')
        st.header('Restablecer contraseña')
        st.caption('Introduce tu usuario y la autorización privada docente para establecer una contraseña nueva.')
        usuario=st.text_input('Usuario docente',max_chars=100,key=f'auth_profesor_recuperacion_usuario_{token}')
        autorizacion=st.text_input('Autorización docente',type='password',autocomplete='off',key=f'auth_profesor_recuperacion_autorizacion_{token}')
        nueva=st.text_input('Nueva contraseña',type='password',autocomplete='new-password',live='300ms',key=f'auth_profesor_recuperacion_clave_{token}')
        mostrar_fortaleza(nueva,usuario=usuario)
        confirmacion=st.text_input('Confirma la nueva contraseña',type='password',autocomplete='new-password',live='300ms',key=f'auth_profesor_recuperacion_confirmar_{token}')
        mostrar_coincidencia(nueva,confirmacion)
        if st.button('Restablecer contraseña',type='primary',width='stretch',key='restablecer_clave_docente'):
            try:
                if not usuario or not autorizacion or not nueva or not confirmacion:
                    raise ValueError('Completa todos los campos para restablecer la contraseña.')
                correcto=restablecer_profesor(usuario,autorizacion,nueva,confirmacion)
            except ValueError as exc:st.warning(str(exc))
            except Exception as exc:
                _logger.error('Fallo de recuperacion docente: tipo=%s',type(exc).__name__)
                st.error('No se pudo confirmar el cambio. Prueba la contraseña nueva antes de repetir la operación.')
            else:
                if correcto:
                    st.session_state['aviso_recuperacion_profesor']='Contraseña restablecida. Las sesiones anteriores se cerraron; inicia sesión con tu contraseña nueva.'
                    cambiar_formulario_profesor('iniciar_sesion');st.rerun()
                else:st.error('Los datos no coinciden o la recuperación está temporalmente bloqueada. Intenta nuevamente más tarde.')
        st.button('Volver al acceso',type='tertiary',on_click=cambiar_formulario_profesor,args=('iniciar_sesion',),key='volver_recuperacion_docente')
    pie_pagina_panel()
