import json
import logging
import time
from hashlib import sha256
from datetime import datetime, timezone

import bcrypt
import oracledb

from src.base_datos.configuracion import obtener_conexion, obtener_pool
from src.utilidades.biometria import validar_vector_facial, normalizar_vector_voz
from src.servicios.validaciones import texto, codigo, usuario as validar_usuario, clave as validar_clave


_logger = logging.getLogger(__name__)


def _contexto_auditoria_actual():
    """Identidad de la sesion de Streamlit; las herramientas sin sesion no inventan actor."""
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    if get_script_run_ctx(suppress_warning=True) is None:
        return None
    from src.utilidades.sesiones import _actor_local
    actor = _actor_local()
    return (actor[0].upper(), actor[1], None) if actor else None


def _preparar_auditoria(conexion):
    with conexion.cursor() as cur:
        cur.callproc("pkg_auditoria.limpiar_contexto")
        contexto = _contexto_auditoria_actual()
        if contexto is not None:
            from src.utilidades.sesiones import _actor_local
            from src.servicios.sesiones_servidor import validar_en_conexion
            validar_en_conexion(conexion, *_actor_local())
            cur.callproc("pkg_auditoria.establecer_contexto", contexto)
        else:
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            if get_script_run_ctx(suppress_warning=True) is not None:
                import streamlit as st
                if st.session_state.get('sesion_iniciada'):
                    from src.servicios.sesiones_servidor import SesionInvalida
                    raise SesionInvalida('La sesión caducó. Inicia sesión nuevamente.')


def _devolver_conexion(conexion):
    pool = obtener_pool()
    try:
        conexion.rollback()
        with conexion.cursor() as cur:
            cur.callproc("pkg_auditoria.limpiar_contexto")
    except Exception:
        # Nunca reutilizar una sesion cuyo actor no se pudo limpiar.
        _logger.exception("Se descarta una conexion porque no fue posible limpiar su contexto de auditoria.")
        pool.drop(conexion)
    else:
        pool.release(conexion)


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
            _preparar_auditoria(conn)
            resultado = operacion(conn)
            return resultado
        except (oracledb.OperationalError, oracledb.InterfaceError) as exc:
            ultimo_error = exc
            if intento == reintentos - 1:
                raise
            time.sleep(espera)
        finally:
            if conn is not None:
                _devolver_conexion(conn)

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
    return json.dumps(list(embedding), allow_nan=False)


def _deserializar_embedding(valor):
    if valor is None:
        return None
    if isinstance(valor, list):
        return valor
    return json.loads(valor)


def _fecha_hora_para_oracle(valor):
    """Oracle recibe el offset explícito; el enlace datetime del driver lo ignora."""
    fecha = datetime.fromisoformat(valor) if isinstance(valor, str) else valor
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.isoformat(timespec="microseconds")


def _fecha_hora_como_texto(valor):
    if valor is None or isinstance(valor, str):
        return valor
    return valor.isoformat()


def cifrar_contrasena(contrasena):
    validar_clave(contrasena)
    return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()


def verificar_contrasena(contrasena, hash_guardado):
    try:
        return bcrypt.checkpw(contrasena.encode(), hash_guardado.encode())
    except (ValueError, TypeError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# Profesores
# ---------------------------------------------------------------------------

def existe_profesor(usuario):
    usuario = validar_usuario(usuario)
    def op(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT profesor_id FROM profesores WHERE LOWER(TRIM(usuario)) = :usuario", usuario=usuario)
            return cur.fetchall()

    return len(ejecutar_con_reintentos(op))


def crear_profesor(usuario, contrasena, nombre):
    from src.servicios.autenticacion import exigir_acceso_disponible
    exigir_acceso_disponible()
    usuario = validar_usuario(usuario)
    nombre = texto(nombre, 'Nombre', 200)
    hash_nuevo = cifrar_contrasena(contrasena)
    def op(conn):
        with conn.cursor() as cur:
            out_id = cur.var(oracledb.NUMBER)
            cur.execute(
                """
                INSERT INTO profesores (usuario, contrasena, nombre)
                VALUES (:usuario, :contrasena, :nombre)
                RETURNING profesor_id INTO :out_id
                """,
                usuario=usuario,
                contrasena=hash_nuevo,
                nombre=nombre,
                out_id=out_id,
            )
            conn.commit()
            return int(out_id.getvalue()[0])

    try:
        profesor_id = ejecutar_con_reintentos(op, reintentos=1)
    except oracledb.IntegrityError as exc:
        if getattr(exc.args[0], 'code', None) == 1:
            raise ValueError('El usuario docente ya existe.') from exc
        raise
    return [{"profesor_id": profesor_id, "usuario": usuario, "nombre": nombre}]


def iniciar_sesion_profesor(usuario, contrasena):
    from src.servicios.autenticacion import exigir_acceso_disponible
    exigir_acceso_disponible()
    usuario = validar_usuario(usuario)
    if not isinstance(contrasena, str) or len(contrasena.encode('utf-8')) > 72:
        return None
    identificador = sha256(usuario.encode('utf-8')).hexdigest()
    def op(conn):
        with conn.cursor() as cur:
            cur.execute("DELETE FROM limites_acceso WHERE ventana_en<SYSTIMESTAMP-INTERVAL '1' DAY AND (bloqueado_hasta IS NULL OR bloqueado_hasta<SYSTIMESTAMP)")
            try:
                cur.execute('INSERT INTO limites_acceso(clave) VALUES(:c)', c=identificador)
            except oracledb.IntegrityError as exc:
                if getattr(exc.args[0], 'code', None) != 1: raise
            cur.execute("""SELECT intentos,CASE WHEN bloqueado_hasta>SYSTIMESTAMP THEN 1 ELSE 0 END,
                CASE WHEN ventana_en<SYSTIMESTAMP-INTERVAL '15' MINUTE THEN 1 ELSE 0 END
                FROM limites_acceso WHERE clave=:c FOR UPDATE""", c=identificador)
            intentos, bloqueado, expirada = cur.fetchone()
            if bloqueado:
                conn.commit()
                return None
            if expirada: intentos = 0
            cur.execute('SELECT profesor_id,usuario,contrasena,nombre FROM profesores WHERE LOWER(TRIM(usuario))=:u AND activo=1', u=usuario)
            profesor = _fila_a_diccionario(cur, cur.fetchone())
            valido = profesor is not None and verificar_contrasena(contrasena, profesor['contrasena'])
            if valido:
                cur.execute('DELETE FROM limites_acceso WHERE clave=:c', c=identificador)
            else:
                cur.execute("""UPDATE limites_acceso SET intentos=:n,
                    ventana_en=CASE WHEN :exp=1 THEN SYSTIMESTAMP ELSE ventana_en END,
                    bloqueado_hasta=CASE WHEN :n>=5 THEN SYSTIMESTAMP+INTERVAL '15' MINUTE END WHERE clave=:c""",
                    n=intentos+1, exp=expirada, c=identificador)
        conn.commit()
        return profesor if valido else None
    return ejecutar_con_reintentos(op, reintentos=1)


# ---------------------------------------------------------------------------
# Estudiantes
# ---------------------------------------------------------------------------

def obtener_todos_estudiantes():
    def op(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT estudiante_id, nombre, codigo_institucional, embedding_facial, embedding_voz FROM estudiantes WHERE activo=1")
            return _filas_a_diccionarios(cur, cur.fetchall())

    estudiantes = ejecutar_con_reintentos(op)
    for e in estudiantes:
        e["embedding_facial"] = _deserializar_embedding(e.get("embedding_facial"))
        e["embedding_voz"] = _deserializar_embedding(e.get("embedding_voz"))
    return estudiantes


def crear_estudiante(nuevo_nombre, embedding_facial=None, embedding_voz=None, *, codigo_institucional=None):
    # Defensa del acceso Python a Oracle, incluso sin pasar por el formulario de registro.
    embedding_facial = validar_vector_facial(embedding_facial).tolist()
    if embedding_voz is not None:
        embedding_voz = normalizar_vector_voz(embedding_voz).tolist()
    nuevo_nombre = texto(nuevo_nombre, 'Nombre', 200)
    codigo_institucional = codigo(codigo_institucional, 'Código institucional')
    def op(conn):
        with conn.cursor() as cur:
            out_id = cur.var(oracledb.NUMBER)
            cur.execute(
                """
                INSERT INTO estudiantes (nombre, codigo_institucional, embedding_facial, embedding_voz)
                VALUES (:nombre, :codigo_institucional, :embedding_facial, :embedding_voz)
                RETURNING estudiante_id INTO :out_id
                """,
                nombre=nuevo_nombre,
                codigo_institucional=codigo_institucional,
                embedding_facial=_serializar_embedding(embedding_facial),
                embedding_voz=_serializar_embedding(embedding_voz),
                out_id=out_id,
            )
            conn.commit()
            return int(out_id.getvalue()[0])

    try:
        estudiante_id = ejecutar_con_reintentos(op, reintentos=1)
    except oracledb.IntegrityError as exc:
        if getattr(exc.args[0], 'code', None) == 1:
            raise ValueError('El código institucional ya tiene un perfil registrado.') from exc
        raise
    return [
        {
            "estudiante_id": estudiante_id,
            "nombre": nuevo_nombre,
            "codigo_institucional": codigo_institucional,
            "embedding_facial": embedding_facial,
            "embedding_voz": embedding_voz,
        }
    ]


# ---------------------------------------------------------------------------
# Materias
# ---------------------------------------------------------------------------

def crear_materia(codigo_materia, nombre, seccion, profesor_id):
    from src.base_datos.gestion import ejecutar
    from src.utilidades.sesiones import obtener_actor
    actor = obtener_actor()
    if actor is None or actor[:2] != ('profesor', profesor_id):
        raise PermissionError('La sesión no corresponde al profesor.')
    codigo_materia = codigo(codigo_materia, 'Código de materia')
    nombre = texto(nombre, 'Nombre', 200)
    seccion = texto(seccion, 'Sección', 100, opcional=True)
    materia_id = ejecutar('crear_materia', [codigo_materia, nombre, seccion], salida=True)
    return [{'materia_id': materia_id, 'codigo_materia': codigo_materia, 'nombre': nombre,
             'seccion': seccion, 'profesor_id': profesor_id}]


def obtener_materia_por_codigo(codigo_materia):
    codigo_materia = codigo(codigo_materia, "Código de materia")
    def op(conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT materia_id, nombre, codigo_materia FROM materias WHERE UPPER(TRIM(codigo_materia)) = :codigo_materia AND activo=1",
                codigo_materia=codigo_materia,
            )
            return _fila_a_diccionario(cur, cur.fetchone())

    return ejecutar_con_reintentos(op)


def obtener_materias_profesor(profesor_id):
    def op(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.materia_id,m.codigo_materia,m.nombre,m.seccion,m.profesor_id,
                       NVL(me.total,0) AS total_estudiantes,NVL(c.total,0) AS total_clases
                FROM materias m
                LEFT JOIN (SELECT materia_id,COUNT(*) total FROM materia_estudiantes GROUP BY materia_id) me
                       ON me.materia_id=m.materia_id
                LEFT JOIN (SELECT materia_id,COUNT(*) total FROM clases WHERE estado='CONFIRMADA' GROUP BY materia_id) c
                       ON c.materia_id=m.materia_id
                WHERE m.profesor_id=:profesor_id AND m.activo=1
                ORDER BY m.materia_id
                """,
                profesor_id=profesor_id,
            )
            return _filas_a_diccionarios(cur, cur.fetchall())

    return ejecutar_con_reintentos(op)


# ---------------------------------------------------------------------------
# Matriculas
# ---------------------------------------------------------------------------

def matricular_estudiante_en_materia(estudiante_id, materia_id):
    from src.base_datos.gestion import ejecutar
    ejecutar('matricular', [estudiante_id, materia_id])
    return [{'estudiante_id': estudiante_id, 'materia_id': materia_id}]


def desmatricular_estudiante_de_materia(estudiante_id, materia_id):
    from src.base_datos.gestion import ejecutar
    return ejecutar('retirar', [estudiante_id, materia_id, 'Retiro solicitado desde la aplicación'])


def esta_estudiante_matriculado(materia_id, estudiante_id):
    def op(conn):
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM materia_estudiantes WHERE materia_id = :materia_id AND estudiante_id = :estudiante_id",
                materia_id=materia_id,
                estudiante_id=estudiante_id,
            )
            return cur.fetchone() is not None

    return ejecutar_con_reintentos(op)


def obtener_materias_estudiante(estudiante_id):
    def op(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.materia_id, m.codigo_materia, m.nombre, m.seccion, m.profesor_id
                FROM materia_estudiantes me
                JOIN materias m ON m.materia_id = me.materia_id
                WHERE me.estudiante_id = :estudiante_id AND m.activo=1
                ORDER BY m.materia_id
                """,
                estudiante_id=estudiante_id,
            )
            filas = _filas_a_diccionarios(cur, cur.fetchall())
            return [{"estudiante_id": estudiante_id, "materia_id": f["materia_id"], "materia": f} for f in filas]

    return ejecutar_con_reintentos(op)


def obtener_estudiantes_matriculados(materia_id):
    def op(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT es.estudiante_id, es.nombre, es.embedding_facial, es.embedding_voz
                FROM materia_estudiantes me
                JOIN estudiantes es ON es.estudiante_id = me.estudiante_id
                WHERE me.materia_id = :materia_id AND es.activo=1
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

def crear_asistencia(registros, profesor_id=None, *, clase_id=None, clave_confirmacion=None, origen=None):
    if clase_id is not None:
        from src.base_datos.clases import confirmar_clase
        return confirmar_clase(registros, profesor_id, clase_id, clave_confirmacion, origen)

    # Compatibilidad de herramientas anteriores: el disparador asigna una clase LEGADO.
    def op(conn):
        with conn.cursor() as cur:
            if profesor_id is not None:
                if not registros or len({r["materia_id"] for r in registros}) != 1:
                    raise ValueError("La propuesta debe pertenecer a una única materia.")
                materia_id = registros[0]["materia_id"]
                cur.execute("SELECT profesor_id FROM materias WHERE materia_id = :m FOR UPDATE", m=materia_id)
                materia = cur.fetchone()
                if materia is None or int(materia[0]) != int(profesor_id):
                    raise PermissionError("Ya no tienes acceso a esta materia. Actualiza el panel.")
                ids = [int(r["estudiante_id"]) for r in registros]
                if len(ids) != len(set(ids)) or any(type(r.get("presente")) is not bool for r in registros):
                    raise ValueError("La propuesta contiene estudiantes duplicados o estados inválidos.")
                cur.execute("SELECT estudiante_id FROM materia_estudiantes WHERE materia_id = :m FOR UPDATE", m=materia_id)
                matriculados = {int(f[0]) for f in cur.fetchall()}
                if set(ids) != matriculados:
                    raise ValueError("La matrícula cambió. Vuelve a ejecutar el análisis antes de confirmar.")
            filas = []
            for registro in registros:
                fh = registro["fecha_hora"]
                filas.append(
                    {
                        "materia_id": registro["materia_id"],
                        "estudiante_id": registro["estudiante_id"],
                        "fecha_hora": _fecha_hora_para_oracle(fh),
                        "presente": 1 if registro.get("presente") else 0,
                    }
                )
            if profesor_id is not None and len({f["fecha_hora"] for f in filas}) != 1:
                raise ValueError("Todos los registros deben pertenecer a una única toma.")
            cur.executemany(
                """
                INSERT INTO registros_asistencia (materia_id, estudiante_id, fecha_hora, presente)
                VALUES (:materia_id, :estudiante_id,
                        TO_TIMESTAMP_TZ(:fecha_hora, 'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM'),
                        :presente)
                """,
                filas,
            )
            conn.commit()
            return len(filas)

    # Una confirmación no se repite automáticamente si se pierde la respuesta del COMMIT.
    return ejecutar_con_reintentos(op, reintentos=1)


def obtener_asistencia_estudiante(estudiante_id):
    def op(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ra.materia_id,ra.clase_id,ra.estudiante_id,
                       TO_CHAR(ra.fecha_hora, 'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') AS fecha_hora,
                       TO_CHAR(c.fecha_hora, 'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') AS fecha_clase,
                       ra.presente,ra.estado_deteccion
                FROM registros_asistencia ra JOIN clases c ON c.clase_id=ra.clase_id
                WHERE ra.estudiante_id = :estudiante_id
                """,
                estudiante_id=estudiante_id,
            )
            return _filas_a_diccionarios(cur, cur.fetchall())

    registros = ejecutar_con_reintentos(op)
    for registro in registros:
        registro["presente"] = bool(registro.get("presente"))
        fh = registro.pop("fecha_hora", None)
        registro["fecha_hora"] = _fecha_hora_como_texto(fh)
    return registros


def obtener_asistencia_profesor(profesor_id):
    def op(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT TO_CHAR(ra.fecha_hora, 'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') AS fecha_hora,
                       TO_CHAR(c.fecha_hora, 'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') AS fecha_clase,
                       ra.clase_id,c.origen,c.lote_legado,ra.presente,ra.corregido_manual,ra.estado_deteccion,
                       m.nombre AS materia_nombre, m.codigo_materia AS codigo_materia
                FROM registros_asistencia ra
                JOIN materias m ON m.materia_id = ra.materia_id
                JOIN clases c ON c.clase_id=ra.clase_id
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
                "fecha_hora": _fecha_hora_como_texto(fh),
                "presente": bool(f.get("presente")),
                "clase_id": f['clase_id'], "fecha_clase": f['fecha_clase'],
                "origen": f['origen'], "lote_legado": f['lote_legado'],
                "corregido_manual": bool(f['corregido_manual']),
                "estado_deteccion": f['estado_deteccion'],
                "materia": {"nombre": f.get("materia_nombre"), "codigo_materia": f.get("codigo_materia")},
            }
        )
    return registros


# ---------------------------------------------------------------------------
# Resúmenes para el dashboard
# ---------------------------------------------------------------------------

def obtener_resumen_profesor(profesor_id):
    def op(conn):
        with conn.cursor() as cur:

            cur.execute(
                "SELECT COUNT(*) FROM materias WHERE profesor_id = :profesor_id AND activo=1",
                profesor_id=profesor_id,
            )
            total_materias = cur.fetchone()[0]

            cur.execute(
                """
                SELECT COUNT(DISTINCT me.estudiante_id)
                FROM materia_estudiantes me
                JOIN materias m ON m.materia_id = me.materia_id
                JOIN estudiantes e ON e.estudiante_id=me.estudiante_id
                WHERE m.profesor_id = :profesor_id AND m.activo=1 AND e.activo=1
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
        with conn.cursor() as cur:

            cur.execute(
                """SELECT COUNT(*) FROM materia_estudiantes me JOIN materias m ON m.materia_id=me.materia_id
                   WHERE me.estudiante_id=:estudiante_id AND m.activo=1""",
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
