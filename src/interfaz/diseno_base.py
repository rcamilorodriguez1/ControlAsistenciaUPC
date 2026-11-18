"""Estilos comunes, locales y cargados antes de las pantallas."""
from pathlib import Path
import streamlit as st

RAIZ = Path(__file__).resolve().parents[2]


def estilo_diseno_base():
    st.html(RAIZ / 'static' / 'css' / 'styles.css')
