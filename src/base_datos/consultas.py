"""Catálogo SQL compartido; los datos se envían al driver mediante parámetros."""
from functools import lru_cache
from pathlib import Path
import re

RAIZ_CONSULTAS = Path(__file__).resolve().parents[2] / 'sql/consultas'
_NOMBRE = re.compile(r'[a-z][a-z0-9_]*(?:/[a-z][a-z0-9_]*)*')
_IDENTIFICADOR = re.compile(r'(?:[A-Za-z][A-Za-z0-9_$#]{0,127}|"[A-Za-z][A-Za-z0-9_$#]{0,127}")')
_MARCADOR = re.compile(r'\{([a-z][a-z0-9_]*)\}')


@lru_cache(maxsize=256)
def cargar_sql(nombre):
    if not isinstance(nombre, str) or not _NOMBRE.fullmatch(nombre):
        raise ValueError('Nombre de consulta no válido.')
    raiz = RAIZ_CONSULTAS.resolve()
    archivo = (raiz / (nombre + '.sql')).resolve()
    if not archivo.is_relative_to(raiz):
        raise ValueError('La consulta debe pertenecer al catálogo SQL.')
    contenido = archivo.read_text(encoding='utf-8')
    if not contenido.strip():
        raise ValueError('La consulta SQL está vacía.')
    return contenido


def sql_con_identificadores(nombre, **identificadores):
    """Solo nombres de esquema/objeto; nunca valores de formularios ni fragmentos SQL."""
    consulta = cargar_sql(nombre)
    if set(_MARCADOR.findall(consulta)) != set(identificadores):
        raise ValueError('Los identificadores no corresponden a la plantilla SQL.')
    for valor in identificadores.values():
        if not isinstance(valor, str) or not _IDENTIFICADOR.fullmatch(valor):
            raise ValueError('Identificador Oracle no válido.')
    return _MARCADOR.sub(lambda coincidencia: identificadores[coincidencia.group(1)], consulta)
