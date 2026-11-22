"""Configuración: entorno > archivo indicado por KEY_FILE > secrets > defecto."""

import os
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def obtener_configuracion(clave, valor_por_defecto=None):
    if clave in os.environ:
        return os.environ[clave]
    archivo = os.environ.get(clave + '_FILE')
    if archivo is not None:
        try:
            return Path(archivo).read_text(encoding='utf-8').rstrip('\r\n')
        except (OSError, UnicodeError, ValueError):
            raise ValueError(f'No se pudo leer el archivo privado de {clave}.') from None
    try:
        return st.secrets.get(clave, valor_por_defecto)
    except StreamlitSecretNotFoundError:
        return valor_por_defecto
