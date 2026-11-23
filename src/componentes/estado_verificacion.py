"""Estado de acceso explícito; no confunde autorización con verificación realizada."""
import streamlit as st
from src.servicios.verificacion_identidad import ESTADOS


def mostrar_estado_verificacion(estado):
    if estado == 'PRUEBA_ACADEMICA':
        st.warning(ESTADOS[estado] + '. Ingreso temporal con clave común para la demostración académica.')
    elif estado == 'EXCEPCIONAL':
        st.warning(ESTADOS[estado] + '. Acceso alternativo autorizado; este acceso no acredita validación biométrica estándar.')
    elif estado == 'BIOMETRICA_COMPLETA':
        st.caption(ESTADOS[estado] + ' · Método facial del acceso actual.')
    else:
        st.caption(ESTADOS['PENDIENTE'] + ' · El siguiente acceso registrará el método utilizado.')
