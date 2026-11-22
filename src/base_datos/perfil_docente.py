"""Perfil docente: identidad y pertenencia contrastadas con el contexto Oracle."""
from src.base_datos import bd
from src.base_datos.consultas import cargar_sql


def consultar_datos(profesor_id):
    def operacion(conn):
        with conn.cursor() as cur:
            cur.execute(cargar_sql('base_datos/perfil_estudiante/operacion_01'))
            if cur.fetchone() != ('PROFESOR', profesor_id):
                raise PermissionError('El perfil requiere el contexto de su docente autenticado.')
            cur.execute(cargar_sql('base_datos/perfil_docente/consultar'), profesor_id=profesor_id)
            return bd._filas_a_diccionarios(cur, cur.fetchall())
    return bd.ejecutar_con_reintentos(operacion)
