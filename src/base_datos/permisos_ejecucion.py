"""Verifica los permisos directos de ejecución contra el contrato SQL compartido."""
from functools import lru_cache
from pathlib import Path
import re

from src.base_datos.consultas import cargar_sql

CONTRATO = Path(__file__).resolve().parents[2] / 'sql/cloud/07_permisos_ejecucion.sql'


@lru_cache(maxsize=1)
def contrato_permisos():
    texto = CONTRATO.read_text(encoding='utf-8')
    sentencias = re.findall(r'^GRANT\b[^;]+;', texto, re.M | re.I)
    permisos = set()
    for sentencia in sentencias:
        coincidencia = re.fullmatch(r'GRANT\s+(SELECT|INSERT|UPDATE|DELETE|EXECUTE)\s*'
            r'(?:\(([A-Za-z_,\s]+)\)\s*)?ON\s+([A-Za-z_]+)\s+TO\s+UPC_AULA_APP\s*;',
            sentencia, re.I)
        if not coincidencia:
            raise ValueError('El contrato de permisos contiene un GRANT no admitido.')
        privilegio, columnas, objeto = coincidencia.groups()
        for columna in columnas.split(',') if columnas else [None]:
            permisos.add((objeto.upper(), privilegio.upper(), columna.strip().upper() if columna else None))
    if not permisos:
        raise ValueError('El contrato de permisos está vacío.')
    return frozenset(permisos)


def comprobar_permisos(cur, esquema):
    cur.execute(cargar_sql('servicios/despliegue/permisos_objetos'), esquema=esquema)
    objetos = cur.fetchall()
    cur.execute(cargar_sql('servicios/despliegue/permisos_columnas'), esquema=esquema)
    columnas = cur.fetchall()
    encontrados = {(objeto, privilegio, None) for objeto, privilegio, _ in objetos}
    encontrados.update((objeto, privilegio, columna) for objeto, columna, privilegio, _ in columnas)
    if encontrados != contrato_permisos() or any(fila[-1] != 'NO' for fila in [*objetos, *columnas]):
        raise ValueError('Los permisos de ejecución difieren del contrato; revisar faltantes, excesos y GRANT OPTION.')
    return len(encontrados)
