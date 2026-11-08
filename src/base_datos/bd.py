import json
import time
from datetime import datetime

import bcrypt
import oracledb

from src.base_datos.configuracion import obtener_conexion, obtener_pool


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def ejecutar_con_reintentos(operacion, reintentos=5, espera=1):
    """Ejecuta `operacion(conexion)` reintentando ante errores transitorios
    de conexion a Oracle."""
    ultimo_error = None
    for intento in range(reintentos):
        conn = None
        try:
            conn = obtener_conexion()
            resultado = operacion(conn)
            return resultado
        except (oracledb.OperationalError, oracledb.InterfaceError) as exc:
            ultimo_error = exc
            if intento == reintentos - 1:
                raise
            time.sleep(espera)
        finally:
            if conn is not None:
                obtener_pool().release(conn)

    raise ultimo_error


def _filas_a_diccionarios(cursor, filas):
    columnas = [c[0].lower() for c in cursor.description]
    return [dict(zip(columnas, fila)) for fila in filas]


def _fila_a_diccionario(cursor, fila):
    if fila is None:
        return None
    columnas = [c[0].lower() for c in cursor.description]
    return dict(zip(columnas, fila))


def _serializar_embedding(embedding):
    if embedding is None:
        return None
    if hasattr(embedding, "tolist"):
        embedding = embedding.tolist()
    return json.dumps(list(embedding))


def _deserializar_embedding(valor):
    if valor is None:
        return None
    if isinstance(valor, list):
        return valor
    return json.loads(valor)


def cifrar_contrasena(contrasena):
    return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()


def verificar_contrasena(contrasena, hash_guardado):
    return bcrypt.checkpw(contrasena.encode(), hash_guardado.encode())


# ---------------------------------------------------------------------------
# Profesores
# ---------------------------------------------------------------------------

def existe_profesor(usuario):
    def op(conn):
        cur = conn.cursor()
        cur.execute("SELECT profesor_id FROM profesores WHERE usuario = :usuario", usuario=usuario)
        return cur.fetchall()

    return len(ejecutar_con_reintentos(op))


def crear_profesor(usuario, contrasena, nombre):
    def op(conn):
        cur = conn.cursor()
        out_id = cur.var(oracledb.NUMBER)
        cur.execute(
            """
            INSERT INTO profesores (usuario, contrasena, nombre)
            VALUES (:usuario, :contrasena, :nombre)
            RETURNING profesor_id INTO :out_id
            """,
            usuario=usuario,
            contrasena=cifrar_contrasena(contrasena),
            nombre=nombre,
            out_id=out_id,
        )
        conn.commit()
        return int(out_id.getvalue()[0])

    profesor_id = ejecutar_con_reintentos(op)
    return [{"profesor_id": profesor_id, "usuario": usuario, "nombre": nombre}]


def iniciar_sesion_profesor(usuario, contrasena):
    def op(conn):
        cur = conn.cursor()
        cur.execute(
            "SELECT profesor_id, usuario, contrasena, nombre FROM profesores WHERE usuario = :usuario",
            usuario=usuario,
        )
        return _fila_a_diccionario(cur, cur.fetchone())

    profesor = ejecutar_con_reintentos(op)
    if profesor and verificar_contrasena(contrasena, profesor["contrasena"]):
        return profesor
    return None


# ---------------------------------------------------------------------------
# Estudiantes
# ---------------------------------------------------------------------------

def obtener_todos_estudiantes():
    def op(conn):
        cur = conn.cursor()
        cur.execute("SELECT estudiante_id, nombre, embedding_facial, embedding_voz FROM estudiantes")
        return _filas_a_diccionarios(cur, cur.fetchall())

    estudiantes = ejecutar_con_reintentos(op)
    for e in estudiantes:
        e["embedding_facial"] = _deserializar_embedding(e.get("embedding_facial"))
        e["embedding_voz"] = _deserializar_embedding(e.get("embedding_voz"))
    return estudiantes


def crear_estudiante(nuevo_nombre, embedding_facial=None, embedding_voz=None):
    def op(conn):
        cur = conn.cursor()
        out_id = cur.var(oracledb.NUMBER)
        cur.execute(
            """
            INSERT INTO estudiantes (nombre, embedding_facial, embedding_voz)
            VALUES (:nombre, :embedding_facial, :embedding_voz)
            RETURNING estudiante_id INTO :out_id
            """,
            nombre=nuevo_nombre,
            embedding_facial=_serializar_embedding(embedding_facial),
            embedding_voz=_serializar_embedding(embedding_voz),
            out_id=out_id,
        )
        conn.commit()
        return int(out_id.getvalue()[0])

    estudiante_id = ejecutar_con_reintentos(op)
    return [
        {
            "estudiante_id": estudiante_id,
            "nombre": nuevo_nombre,
            "embedding_facial": embedding_facial,
            "embedding_voz": embedding_voz,
        }
    ]


# ---------------------------------------------------------------------------
# Materias
# ---------------------------------------------------------------------------

def crear_materia(codigo_materia, nombre, seccion, profesor_id):
    def op(conn):
        cur = conn.cursor()
        out_id = cur.var(oracledb.NUMBER)
        cur.execute(
            """
            INSERT INTO materias (codigo_materia, nombre, seccion, profesor_id)
            VALUES (:codigo_materia, :nombre, :seccion, :profesor_id)
            RETURNING materia_id INTO :out_id
            """,
            codigo_materia=codigo_materia,
            nombre=nombre,
            seccion=seccion,
            profesor_id=profesor_id,
            out_id=out_id,
        )
        conn.commit()
        return int(out_id.getvalue()[0])

    materia_id = ejecutar_con_reintentos(op)
    return [
        {
            "materia_id": materia_id,
            "codigo_materia": codigo_materia,
            "nombre": nombre,
            "seccion": seccion,
            "profesor_id": profesor_id,
        }
    ]


def obtener_materia_por_codigo(codigo_materia):
    def op(conn):
        cur = conn.cursor()
        cur.execute(
            "SELECT materia_id, nombre, codigo_materia FROM materias WHERE codigo_materia = :codigo_materia",
            codigo_materia=codigo_materia,
        )
        return _fila_a_diccionario(cur, cur.fetchone())

    return ejecutar_con_reintentos(op)


def obtener_materias_profesor(profesor_id):
    def op(conn):
        cur = conn.cursor()
        cur.execute(
            """
            SELECT materia_id, codigo_materia, nombre, seccion, profesor_id
            FROM materias
            WHERE profesor_id = :profesor_id
            ORDER BY materia_id
            """,
            profesor_id=profesor_id,
        )
        materias = _filas_a_diccionarios(cur, cur.fetchall())

        for materia in materias:
            cur.execute(
                "SELECT COUNT(*) FROM materia_estudiantes WHERE materia_id = :materia_id",
                materia_id=materia["materia_id"],
            )
            materia["total_estudiantes"] = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(DISTINCT fecha_hora) FROM registros_asistencia WHERE materia_id = :materia_id",
                materia_id=materia["materia_id"],
            )
            materia["total_clases"] = cur.fetchone()[0]

        return materias

    return ejecutar_con_reintentos(op)


# ---------------------------------------------------------------------------
# Matriculas
# ---------------------------------------------------------------------------

def matricular_estudiante_en_materia(estudiante_id, materia_id):
    def op(conn):
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO materia_estudiantes (estudiante_id, materia_id) VALUES (:estudiante_id, :materia_id)",
            estudiante_id=estudiante_id,
            materia_id=materia_id,
        )
        conn.commit()

    ejecutar_con_reintentos(op)
    return [{"estudiante_id": estudiante_id, "materia_id": materia_id}]


def desmatricular_estudiante_de_materia(estudiante_id, materia_id):
    def op(conn):
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM materia_estudiantes WHERE estudiante_id = :estudiante_id AND materia_id = :materia_id",
            estudiante_id=estudiante_id,
            materia_id=materia_id,
        )
        conn.commit()
        return cur.rowcount

    return ejecutar_con_reintentos(op)


def esta_estudiante_matriculado(materia_id, estudiante_id):
    def op(conn):
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM materia_estudiantes WHERE materia_id = :materia_id AND estudiante_id = :estudiante_id",
            materia_id=materia_id,
            estudiante_id=estudiante_id,
        )
        return cur.fetchone() is not None

    return ejecutar_con_reintentos(op)


def obtener_materias_estudiante(estudiante_id):
    def op(conn):
        cur = conn.cursor()
        cur.execute(
            """
            SELECT m.materia_id, m.codigo_materia, m.nombre, m.seccion, m.profesor_id
            FROM materia_estudiantes me
            JOIN materias m ON m.materia_id = me.materia_id
            WHERE me.estudiante_id = :estudiante_id
            ORDER BY m.materia_id
            """,
            estudiante_id=estudiante_id,
        )
        filas = _filas_a_diccionarios(cur, cur.fetchall())
        return [{"estudiante_id": estudiante_id, "materia_id": f["materia_id"], "materia": f} for f in filas]

    return ejecutar_con_reintentos(op)


def obtener_estudiantes_matriculados(materia_id):
    def op(conn):
        cur = conn.cursor()
        cur.execute(
            """
            SELECT es.estudiante_id, es.nombre, es.embedding_facial, es.embedding_voz
            FROM materia_estudiantes me
            JOIN estudiantes es ON es.estudiante_id = me.estudiante_id
            WHERE me.materia_id = :materia_id
            ORDER BY es.nombre
            """,
            materia_id=materia_id,
        )
        return _filas_a_diccionarios(cur, cur.fetchall())

    estudiantes = ejecutar_con_reintentos(op)
    for e in estudiantes:
        e["embedding_facial"] = _deserializar_embedding(e.get("embedding_facial"))
        e["embedding_voz"] = _deserializar_embedding(e.get("embedding_voz"))
    return estudiantes


# ---------------------------------------------------------------------------
# Asistencia
# ---------------------------------------------------------------------------

def crear_asistencia(registros):
    def op(conn):
        cur = conn.cursor()
        filas = []
        for registro in registros:
            fh = registro["fecha_hora"]
            fh_dt = datetime.fromisoformat(fh) if isinstance(fh, str) else fh
            filas.append(
                {
                    "materia_id": registro["materia_id"],
                    "estudiante_id": registro["estudiante_id"],
                    "fecha_hora": fh_dt,
                    "presente": 1 if registro.get("presente") else 0,
                }
            )
        cur.executemany(
            """
            INSERT INTO registros_asistencia (materia_id, estudiante_id, fecha_hora, presente)
            VALUES (:materia_id, :estudiante_id, :fecha_hora, :presente)
            """,
            filas,
        )
        conn.commit()
        return len(filas)

    return ejecutar_con_reintentos(op)


def obtener_asistencia_estudiante(estudiante_id):
    def op(conn):
        cur = conn.cursor()
        cur.execute(
            """
            SELECT materia_id, estudiante_id, fecha_hora, presente
            FROM registros_asistencia
            WHERE estudiante_id = :estudiante_id
            """,
            estudiante_id=estudiante_id,
        )
        return _filas_a_diccionarios(cur, cur.fetchall())

    registros = ejecutar_con_reintentos(op)
    for registro in registros:
        registro["presente"] = bool(registro.get("presente"))
        fh = registro.pop("fecha_hora", None)
        registro["fecha_hora"] = fh.isoformat() if fh is not None else None
    return registros


def obtener_asistencia_profesor(profesor_id):
    def op(conn):
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ra.fecha_hora, ra.presente,
                   m.nombre AS materia_nombre, m.codigo_materia AS codigo_materia
            FROM registros_asistencia ra
            JOIN materias m ON m.materia_id = ra.materia_id
            WHERE m.profesor_id = :profesor_id
            ORDER BY ra.fecha_hora DESC
            """,
            profesor_id=profesor_id,
        )
        return _filas_a_diccionarios(cur, cur.fetchall())

    filas = ejecutar_con_reintentos(op)
    registros = []
    for f in filas:
        fh = f.get("fecha_hora")
        registros.append(
            {
                "fecha_hora": fh.isoformat() if fh is not None else None,
                "presente": bool(f.get("presente")),
                "materia": {"nombre": f.get("materia_nombre"), "codigo_materia": f.get("codigo_materia")},
            }
        )
    return registros


# ---------------------------------------------------------------------------
# Resúmenes para el dashboard
# ---------------------------------------------------------------------------

def obtener_resumen_profesor(profesor_id):
    def op(conn):
        cur = conn.cursor()

        cur.execute(
            "SELECT COUNT(*) FROM materias WHERE profesor_id = :profesor_id",
            profesor_id=profesor_id,
        )
        total_materias = cur.fetchone()[0]

        cur.execute(
            """
            SELECT COUNT(DISTINCT me.estudiante_id)
            FROM materia_estudiantes me
            JOIN materias m ON m.materia_id = me.materia_id
            WHERE m.profesor_id = :profesor_id
            """,
            profesor_id=profesor_id,
        )
        total_estudiantes = cur.fetchone()[0]

        cur.execute(
            """
            SELECT ROUND(AVG(CASE WHEN ra.presente = 1 THEN 100 ELSE 0 END))
            FROM registros_asistencia ra
            JOIN materias m ON m.materia_id = ra.materia_id
            WHERE m.profesor_id = :profesor_id
            """,
            profesor_id=profesor_id,
        )
        promedio = cur.fetchone()[0]

        return {
            "total_materias": total_materias,
            "total_estudiantes": total_estudiantes,
            "asistencia_promedio": float(promedio) if promedio is not None else 0.0,
        }

    return ejecutar_con_reintentos(op)


def obtener_resumen_estudiante(estudiante_id):
    def op(conn):
        cur = conn.cursor()

        cur.execute(
            "SELECT COUNT(*) FROM materia_estudiantes WHERE estudiante_id = :estudiante_id",
            estudiante_id=estudiante_id,
        )
        total_materias = cur.fetchone()[0]

        cur.execute(
            """
            SELECT COUNT(*), SUM(CASE WHEN presente = 1 THEN 1 ELSE 0 END)
            FROM registros_asistencia
            WHERE estudiante_id = :estudiante_id
            """,
            estudiante_id=estudiante_id,
        )
        total_clases, total_presentes = cur.fetchone()
        total_clases = total_clases or 0
        total_presentes = total_presentes or 0

        promedio = round((total_presentes / total_clases) * 100) if total_clases else 0

        return {
            "total_materias": total_materias,
            "total_clases": total_clases,
            "asistencia_promedio": float(promedio),
        }

    return ejecutar_con_reintentos(op)
