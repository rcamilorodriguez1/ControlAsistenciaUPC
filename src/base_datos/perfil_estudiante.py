"""Lectura privada del perfil académico con el contexto validado de Oracle."""
from src.base_datos import bd
from src.base_datos.consultas import cargar_sql


def consultar_datos(estudiante_id):
    def operacion(conn):
        with conn.cursor() as cur:
            cur.execute(cargar_sql('base_datos/perfil_estudiante/operacion_01'))
            if cur.fetchone() != ('ESTUDIANTE', estudiante_id):
                raise PermissionError('El perfil solo puede consultar los datos de su estudiante autenticado.')
            cur.execute(cargar_sql('base_datos/perfil_estudiante/operacion_02'), estudiante_id=estudiante_id)
            return bd._filas_a_diccionarios(cur, cur.fetchall())
    return bd.ejecutar_con_reintentos(operacion)
