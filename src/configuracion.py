"""Configuración compartida: entorno del proceso > secrets de Streamlit > defecto."""

import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def obtener_configuracion(clave, valor_por_defecto=None):
    if clave in os.environ:
        return os.environ[clave]
    try:
        return st.secrets.get(clave, valor_por_defecto)
    except StreamlitSecretNotFoundError:
        return valor_por_defecto
