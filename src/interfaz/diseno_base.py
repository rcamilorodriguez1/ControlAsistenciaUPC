"""Estilos comunes, locales y cargados antes de las pantallas."""
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from urllib.parse import quote
import streamlit as st

RAIZ = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def _fuente_iconos():
    """Reutiliza el WOFF2 local de la versión instalada, sin copiarlo ni usar un CDN."""
    carpeta = Path(st.__file__).resolve().parent / 'static' / 'static' / 'media'
    archivos = sorted(carpeta.glob('MaterialSymbols-Rounded.*.woff2'))
    if not archivos:
        return None  # Otras distribuciones conservan la fuente nativa de Streamlit.
    fuente = archivos[0]
    return fuente.name, sha256(fuente.read_bytes()).hexdigest()[:16]


def estilo_diseno_base():
    estilos = (RAIZ / 'static' / 'css' / 'styles.css').read_text(encoding='utf-8')
    fuente = _fuente_iconos()
    if fuente:
        nombre, huella = fuente
        base = quote(st.get_option('server.baseUrlPath').strip('/'), safe='/')
        ruta = '/' + '/'.join(p for p in (base, 'static/media', quote(nombre)) if p)
        # La URL versionada no reutiliza una respuesta fallida/caducada de la fuente nativa.
        estilos = ('@font-face {font-family:"UPC Material Symbols Rounded";'
                   'font-style:normal;font-weight:400;font-display:block;'
                   f'src:url("{ruta}?upc_iconos={huella}") format("woff2");}}\n' + estilos)
    st.html('<style>' + estilos + '</style>')
