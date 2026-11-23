"""Acceso administrativo separado: vistas de auditoría y operaciones PL/SQL autorizadas."""
import csv
from functools import lru_cache
from hashlib import sha256
from io import StringIO
import re
from threading import Lock

import bcrypt
import oracledb

from src.base_datos import bd
from src.configuracion import obtener_configuracion
from src.base_datos.transporte import parametros_transporte
from src.servicios.validaciones import texto, codigo, usuario as validar_usuario
from src.base_datos.consultas import cargar_sql, sql_con_identificadores
from src.base_datos.esquema import esquema_propietario

_pool = None
_lock = Lock()


def propietario():
    return '"' + esquema_propietario() + '"'


def obtener_pool_admin():
    global _pool
    with _lock:
        if _pool is None:
            usuario = obtener_configuracion('ORACLE_ADMIN_USUARIO')
            clave = obtener_configuracion('ORACLE_ADMIN_CONTRASENA')
            if not usuario or not clave: raise ValueError('Falta preparar el acceso Oracle administrativo.')
            minimo = int(obtener_configuracion('ORACLE_ADMIN_POOL_MINIMO', 0))
            maximo = int(obtener_configuracion('ORACLE_ADMIN_POOL_MAXIMO', 4))
            if minimo < 0 or maximo < max(1, minimo):
                raise ValueError('Límites del pool administrativo no válidos.')
            _pool = oracledb.create_pool(user=usuario, password=clave,
                dsn=obtener_configuracion('ORACLE_DSN', 'localhost:1521/XEPDB1'),
                min=minimo, max=maximo, increment=1, **parametros_transporte())
    return _pool


@lru_cache(maxsize=1)
def _hash_simulado():
    return bcrypt.hashpw(b'comparacion-local-sin-cuenta', bcrypt.gensalt()).decode()


def autenticar(usuario, contrasena):
    from src.servicios.autenticacion import exigir_acceso_disponible
    exigir_acceso_disponible()
    usuario = validar_usuario(usuario)
    if not isinstance(contrasena, str) or len(contrasena.encode('utf-8')) > 72: return None
    llave = sha256(('administrador:' + usuario).encode()).hexdigest()
    def op(conn):
        with conn.cursor() as cur:
            cur.execute(cargar_sql('compartidas/limpiar_limites_expirados'))
            try: cur.execute(cargar_sql('compartidas/crear_limite'), c=llave)
            except oracledb.IntegrityError as exc:
                if exc.args[0].code != 1: raise
            cur.execute(cargar_sql('compartidas/consultar_limites'), c=llave)
            intentos, bloqueado, expirada = cur.fetchone()
            if bloqueado:
                conn.commit(); return None
            if expirada: intentos = 0
            cur.execute(cargar_sql('base_datos/administracion/autenticar_03'), u=usuario)
            perfil = bd._fila_a_diccionario(cur, cur.fetchone())
            correcto = bd.verificar_contrasena(contrasena, perfil['contrasena'] if perfil else _hash_simulado()) and perfil is not None
            if correcto:
                cur.execute(cargar_sql('compartidas/limpiar_limite'), c=llave)
                cur.execute(cargar_sql('base_datos/administracion/autenticar_06'), a=perfil['administrador_id'])
                perfil.pop('contrasena', None)
            else:
                cur.execute(cargar_sql('compartidas/registrar_fallo_acceso'), n=intentos+1, exp=expirada, c=llave)
        conn.commit()
        return perfil if correcto else None
    return bd.ejecutar_con_reintentos(op, reintentos=1)


def _actor():
    from src.utilidades.sesiones import obtener_actor
    actor = obtener_actor(renovar=True)
    if actor is None:
        import streamlit as st
        from src.servicios.sesiones_servidor import SesionInvalida
        raise SesionInvalida(st.session_state.get('aviso_sesion','Se requiere una sesión administrativa.'))
    if actor[0] != 'administrador': raise PermissionError('Se requiere una sesión administrativa.')
    return actor


def _ejecutar(operacion, *, escritura=False):
    actor = _actor()
    pool = obtener_pool_admin()
    conn = pool.acquire()
    limpiar = True
    try:
        from src.servicios.sesiones_servidor import validar_en_conexion
        validar_en_conexion(conn,*actor,esquema=propietario()+'.')
        with conn.cursor() as cur:
            cur.callproc(propietario() + '.pkg_auditoria.limpiar_contexto')
            cur.callproc(propietario() + '.pkg_auditoria.establecer_contexto', ['ADMINISTRADOR', actor[1], None])
        resultado = operacion(conn)
        if escritura: conn.commit()
        return resultado
    except oracledb.Error as exc:
        cod = getattr(exc.args[0], 'code', None)
        if cod in (20101, 20064): raise PermissionError('La cuenta administrativa ya no está activa o no tiene permiso.') from exc
        if cod == 1: raise ValueError('El usuario, el código o el documento ya está en uso.') from exc
        if cod in (20102, 20103, 20106, 20301, 20302, 20303, 20313, 1403):
            mensaje = 'El registro ya no existe.' if cod == 1403 else str(exc.args[0]).splitlines()[0].split(': ', 1)[-1]
            raise ValueError(mensaje) from exc
        raise
    finally:
        try:
            conn.rollback()
            with conn.cursor() as cur: cur.callproc(propietario() + '.pkg_auditoria.limpiar_contexto')
        except Exception:
            limpiar = False; pool.drop(conn)
        if limpiar: pool.release(conn)


def _cursor(procedimiento, parametros):
    def op(conn):
        with conn.cursor() as cur, conn.cursor() as datos:
            cur.callproc(propietario() + '.pkg_administracion.' + procedimiento, [*parametros, datos])
            return bd._filas_a_diccionarios(datos, datos.fetchall())
    return _ejecutar(op)


def cuentas(tipo, busqueda=''):
    if tipo not in ('PROFESOR', 'ESTUDIANTE'): raise ValueError('Tipo de cuenta no válido.')
    return _cursor('cuentas', [tipo, texto(busqueda, 'Búsqueda', 100, opcional=True)])


def materias(busqueda=''):
    return _cursor('listar_materias', [texto(busqueda, 'Búsqueda', 100, opcional=True)])


def auditoria(tipo, desde, hasta, limite=500):
    if tipo not in ('ASISTENCIA', 'MATRICULAS', 'GESTION'): raise ValueError('Tipo de auditoría no válido.')
    if type(limite) is not int or not 1 <= limite <= 10000 or hasta <= desde: raise ValueError('Intervalo o límite no válido.')
    def op(conn):
        with conn.cursor() as cur, conn.cursor() as datos:
            cur.execute(sql_con_identificadores('base_datos/administracion/auditoria', esquema=propietario()),
                tipo=tipo, desde=bd._fecha_hora_para_oracle(desde), hasta=bd._fecha_hora_para_oracle(hasta), limite=limite, salida=datos)
            return bd._filas_a_diccionarios(datos, datos.fetchall())
    return _ejecutar(op)


def _escritura(procedimiento, parametros):
    def op(conn):
        with conn.cursor() as cur: cur.callproc(propietario() + '.pkg_administracion.' + procedimiento, parametros)
    return _ejecutar(op, escritura=True)


def editar_profesor(identificador, usuario, nombre, activo, motivo, nueva_clave='', *, version):
    _actor()
    hashed = bd.cifrar_contrasena(nueva_clave) if nueva_clave else None
    return _escritura('editar_profesor', [int(identificador), validar_usuario(usuario), texto(nombre, 'Nombre', 200),
        int(bool(activo)), hashed, texto(motivo, 'Motivo', 500), version])


def editar_estudiante(identificador, codigo_institucional, nombre, activo, motivo, *, version):
    resultado = _escritura('editar_estudiante', [int(identificador), codigo(codigo_institucional, 'Código institucional') if codigo_institucional.strip() else None,
        texto(nombre, 'Nombre', 200), int(bool(activo)), texto(motivo, 'Motivo', 500), version])
    from src.servicios.biometria_diferida import invalidar_modelo_facial
    invalidar_modelo_facial()
    return resultado


def editar_materia(identificador, codigo_materia, nombre, seccion, profesor, activo, motivo, *, version):
    return _escritura('editar_materia', [int(identificador), codigo(codigo_materia, 'Código de materia'),
        texto(nombre, 'Nombre', 200), texto(seccion, 'Sección', 100, opcional=True), int(profesor), int(bool(activo)), texto(motivo, 'Motivo', 500), version])


def exportar_csv(tipo, filas):
    _actor()
    if tipo not in ('ASISTENCIA', 'MATRICULAS', 'GESTION') or len(filas)>10000: raise ValueError('Exportación no válida.')
    salida = StringIO(newline='')
    def segura(valor):
        if isinstance(valor, str) and valor.lstrip().startswith(('=', '+', '-', '@')): return "'" + valor
        return valor
    columnas = list(filas[0]) if filas else []
    escritor = csv.writer(salida)
    escritor.writerow(columnas)
    for fila in filas: escritor.writerow([segura(fila.get(c)) for c in columnas])
    _escritura('registrar_exportacion', [tipo, len(filas)])
    return salida.getvalue().encode('utf-8-sig')
