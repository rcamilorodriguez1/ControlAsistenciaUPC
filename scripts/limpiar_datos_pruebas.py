"""Vacía datos del proyecto con respaldo previo; sin --aplicar solo cuenta filas."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import tomllib
from uuid import uuid4

import oracledb
from _comun import RAIZ, usar_entorno


# Hijas antes que padres. Los historiales van al final porque los DELETE disparan auditoría.
ORDEN_BORRADO = (
    'VERIFICACION_ESTUDIANTES', 'REGISTROS_ASISTENCIA', 'MATERIA_ESTUDIANTES',
    'CLASES', 'MATERIAS', 'ESTUDIANTES', 'PROFESORES', 'ADMINISTRADORES',
    'SESIONES_USUARIO', 'LIMITES_ACCESO', 'AUDITORIA_ASISTENCIA',
    'HISTORIAL_MATRICULAS', 'EVENTOS_GESTION',
)
TABLAS = frozenset((*ORDEN_BORRADO, 'VERSIONES_ESQUEMA'))


def abrir(config):
    return oracledb.connect(user=config['ORACLE_USUARIO'], password=config['ORACLE_CONTRASENA'],
                           dsn=config['ORACLE_DSN'], tcp_connect_timeout=15)


def inspeccionar(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT USER,SYS_CONTEXT('USERENV','CURRENT_SCHEMA'),SYS_CONTEXT('USERENV','DB_NAME'),SYS_CONTEXT('USERENV','CON_NAME') FROM dual")
        usuario, esquema, base, contenedor = cur.fetchone()
        if usuario != 'UPC_ASISTENCIA' or esquema != usuario:
            raise ValueError('La limpieza requiere el propietario UPC_ASISTENCIA de la base del proyecto.')
        cur.execute('SELECT table_name FROM user_tables')
        if {r[0] for r in cur} != TABLAS:
            raise ValueError('Las tablas no coinciden exactamente con las catorce del proyecto; no se limpia.')
        cur.execute('SELECT version,descripcion,aplicado_en FROM versiones_esquema ORDER BY version')
        versiones = [tuple(str(v) for v in r) for r in cur]
        if [v[0] for v in versiones] != [f'{i:03d}' for i in range(1,12)]:
            raise ValueError('Se requiere el esquema 001–011 verificado.')
    return (base, contenedor), versiones


def contar(conn):
    resultado = {}
    with conn.cursor() as cur:
        for tabla in sorted(TABLAS):
            cur.execute('SELECT COUNT(*) FROM '+tabla)
            resultado[tabla] = int(cur.fetchone()[0])
    return resultado


def bloquear(conn):
    with conn.cursor() as cur:
        cur.execute('LOCK TABLE '+','.join(sorted(TABLAS))+' IN EXCLUSIVE MODE NOWAIT')


def crear_respaldo(config, destino):
    from src.base_datos.recuperacion import respaldar, verificar, clave_local
    clave = clave_local(RAIZ/'.local/clave_respaldos.bin', crear=True)
    with abrir(config) as conn:
        respaldar(conn,destino,clave)
    verificar(destino,clave)


def borrar(conn):
    eliminadas = {}
    with conn.cursor() as cur:
        cur.callproc('pkg_auditoria.establecer_contexto',
                     ['SISTEMA',None,'Reinicio de datos para aprendizaje y presentacion, autorizado por el responsable.'])
        for tabla in ORDEN_BORRADO:
            cur.execute('DELETE FROM '+tabla)
            eliminadas[tabla] = cur.rowcount
        cur.callproc('pkg_auditoria.limpiar_contexto')
    return eliminadas


def verificar_limpieza(conn, versiones_originales):
    _,versiones = inspeccionar(conn)
    conteo = contar(conn)
    if versiones != versiones_originales or any(conteo[t] for t in ORDEN_BORRADO):
        raise RuntimeError('La limpieza no cumple el estado esperado; se revierte.')
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM user_objects WHERE status='INVALID'")
        if cur.fetchone()[0]:raise RuntimeError('Hay objetos invalidos; se revierte.')
        cur.execute("SELECT COUNT(*) FROM user_triggers WHERE status<>'ENABLED'")
        if cur.fetchone()[0]:raise RuntimeError('Hay triggers deshabilitados; se revierte.')
    return conteo


def ejecutar_planes(planes, carpeta):
    """Todos los respaldos antes de borrar; todos los estados verificados antes de COMMIT."""
    try:
        for p in planes:
            bloquear(p['conn'])
        for p in planes:
            p['antes'] = contar(p['conn'])
            p['respaldo'] = str(carpeta/('respaldo_'+p['nombre']))
            crear_respaldo(p['config'],Path(p['respaldo']))
            print(p['nombre']+': respaldo cifrado verificado.',flush=True)
        for p in planes:
            p['eliminadas'] = borrar(p['conn'])
            p['despues'] = verificar_limpieza(p['conn'],p['versiones'])
        for p in planes:
            p['conn'].commit()
            p['confirmada'] = True
            print(p['nombre']+': 13 tablas de datos vacias; esquema y versiones conservados.',flush=True)
    except Exception:
        for p in planes:
            if not p.get('confirmada'):
                p['conn'].rollback()
        raise


def main():
    usar_entorno()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',action='append',required=True,metavar='NOMBRE=PERFIL_TOML',
                        help='Repetir para local y autonomous; perfiles privados del propietario.')
    parser.add_argument('--aplicar',action='store_true',help='Respaldar y vaciar datos; sin esta opción solo consulta.')
    args = parser.parse_args()
    with ExitStack() as pila:
        planes=[]; identidades=set(); nombres=set()
        for entrada in args.base:
            nombre,sep,ruta=entrada.partition('=')
            if not sep or not re.fullmatch(r'[a-z][a-z0-9_]{0,29}',nombre) or nombre in nombres:
                parser.error('Usa un nombre distinto y valido para cada perfil.')
            nombres.add(nombre)
            config=tomllib.loads(Path(ruta).read_text(encoding='utf-8'))
            conn=pila.enter_context(abrir(config))
            identidad,versiones=inspeccionar(conn)
            if identidad in identidades:raise ValueError('Dos perfiles apuntan a la misma base; no se limpia.')
            identidades.add(identidad)
            planes.append({'nombre':nombre,'config':config,'conn':conn,'versiones':versiones})
        if not args.aplicar:
            for p in planes:print(json.dumps({'base':p['nombre'],'filas':contar(p['conn']),'solo_consulta':True}))
            return
        carpeta=RAIZ/'.local/reinicios'/('academico_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:6])
        carpeta.mkdir(parents=True,exist_ok=False)
        try:
            ejecutar_planes(planes,carpeta)
        finally:
            informe={'fecha_utc':datetime.now(timezone.utc).isoformat(),
                     'bases':[{k:v for k,v in p.items() if k not in ('config','conn','versiones')} for p in planes]}
            (carpeta/'resultado.json').write_text(json.dumps(informe,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Evidencia privada:',(carpeta/'resultado.json').relative_to(RAIZ),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        codigo=getattr(exc.args[0],'code',None) if exc.args else None
        mensaje=str(exc) if isinstance(exc,(ValueError,RuntimeError)) else type(exc).__name__+(f' (Oracle {codigo})' if codigo else '')
        raise SystemExit('No se completo la limpieza: '+mensaje) from None
