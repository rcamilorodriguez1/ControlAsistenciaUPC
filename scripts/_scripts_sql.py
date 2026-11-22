"""Lector del subconjunto SQL*Plus usado por el instalador del repositorio.

No implementa un intérprete SQL*Plus general. Rechaza comandos desconocidos,
inclusiones cíclicas, sustituciones y sentencias sin terminador.
"""
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class Sentencia:
    archivo: Path
    linea: int
    sql: str


_PLSQL = re.compile(r'^(?:DECLARE\b|BEGIN\b|CREATE\s+(?:OR\s+REPLACE\s+)?(?:PACKAGE|PROCEDURE|FUNCTION|TRIGGER|TYPE)\b)', re.I)
_DIRECTIVA = re.compile(r'^(?:SET\s+(?:ECHO|VERIFY|DEFINE|SERVEROUTPUT|LINESIZE|PAGESIZE|AUTOCOMMIT)\b|WHENEVER\s+(?:SQLERROR|OSERROR)\b|PROMPT\b|SHOW\s+ERRORS\b)', re.I)
_SQL = re.compile(r'^(?:CREATE|ALTER|DROP|GRANT|REVOKE|COMMENT|SELECT|WITH|INSERT|UPDATE|DELETE|MERGE|COMMIT|ROLLBACK|DECLARE|BEGIN)\b', re.I)


def leer_script(archivo, raiz, pila=()):
    raiz = Path(raiz).resolve()
    archivo = Path(archivo).resolve()
    if not archivo.is_relative_to(raiz) or archivo in pila:
        raise ValueError('Inclusión SQL fuera del proyecto o cíclica.')
    if not archivo.is_file():
        raise ValueError('Falta un archivo del instalador SQL.')
    buffer = []
    inicio = 0
    plsql = False
    for numero, linea in enumerate(archivo.read_text(encoding='utf-8-sig').splitlines(), 1):
        texto = linea.strip()
        if not buffer:
            if not texto or texto.startswith('--'):
                continue
            if texto.startswith('@'):
                relativo = texto.startswith('@@')
                ruta = texto[2 if relativo else 1:].strip().strip('"')
                if not ruta or '&' in ruta:
                    raise ValueError(f'Inclusión no admitida en {archivo.name}:{numero}.')
                yield from leer_script((archivo.parent if relativo else raiz) / ruta,
                                      raiz, (*pila, archivo))
                continue
            if _DIRECTIVA.match(texto):
                if re.match(r'SET\s+DEFINE\s+ON\b', texto, re.I):
                    raise ValueError('No se admite sustitución de variables SQL*Plus.')
                continue
            if not _SQL.match(texto):
                raise ValueError(f'Comando no admitido en {archivo.name}:{numero}.')
            inicio = numero
            plsql = bool(_PLSQL.match(texto))
        if texto == '/':
            if not plsql or not buffer:
                raise ValueError(f'Terminador inesperado en {archivo.name}:{numero}.')
            yield Sentencia(archivo, inicio, '\n'.join(buffer).strip())
            buffer = []
            continue
        buffer.append(linea)
        # Los archivos del proyecto delimitan SQL al final de la línea y PL/SQL con /.
        # No dividir bloques por los puntos y coma internos de BEGIN/END ni q'~...~'.
        if not plsql and texto.endswith(';'):
            yield Sentencia(archivo, inicio, '\n'.join(buffer).strip()[:-1])
            buffer = []
    if buffer:
        raise ValueError(f'Sentencia incompleta en {archivo.name}:{inicio}.')


def ejecutar_script(conexion, plan, *, informar=lambda mensaje: None):
    with conexion.cursor() as cursor:
        for sentencia in plan:
            informar(f'{sentencia.archivo.name}:{sentencia.linea}')
            try:
                cursor.execute(sentencia.sql)
            except Exception as exc:
                # No incluir la sentencia ni valores privados en el mensaje.
                raise RuntimeError(f'Falló {sentencia.archivo.name}:{sentencia.linea}.') from exc
