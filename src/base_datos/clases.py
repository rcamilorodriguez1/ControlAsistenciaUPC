"""Operaciones de clase delegadas a PL/SQL, con contexto de profesor y transaccion explicita."""

import json

import oracledb

from src.base_datos import bd


def _comprobar_actor(cur, profesor_id):
    cur.execute('SELECT pkg_auditoria.rol_actual,pkg_auditoria.actor_actual FROM dual')
    rol, actor = cur.fetchone()
    if rol != 'PROFESOR' or actor != profesor_id:
        raise PermissionError('La sesión de profesor cambió. Vuelve a iniciar sesión.')


def _traducir_error(exc):
    codigo = getattr(exc.args[0], 'code', None)
    if codigo in (20071, 20072):
        raise PermissionError('Ya no tienes acceso a esta materia. Actualiza el panel.') from exc
    if codigo in range(20073, 20080):
        mensaje = str(exc.args[0]).splitlines()[0].split(': ', 1)[-1]
        raise ValueError(mensaje) from exc
    raise exc


def abrir_clase(materia_id, profesor_id, fecha_hora):
    fecha = bd._fecha_hora_para_oracle(fecha_hora)

    def op(conn):
        try:
            with conn.cursor() as cur:
                _comprobar_actor(cur, profesor_id)
                salida = cur.var(oracledb.NUMBER)
                cur.execute('''BEGIN pkg_clases.abrir_clase(:m,
                    TO_TIMESTAMP_TZ(:f,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM'),:id); END;''',
                    m=materia_id, f=fecha, id=salida)
                clase_id = int(salida.getvalue())
            conn.commit()
            return clase_id
        except Exception:
            conn.rollback()
            raise
    try:
        # Abrir por materia/instante es idempotente aunque se pierda una respuesta.
        return bd.ejecutar_con_reintentos(op)
    except oracledb.Error as exc:
        _traducir_error(exc)


def obtener_clases_profesor(materia_id, profesor_id):
    def op(conn):
        with conn.cursor() as cur:
            cur.execute('''SELECT c.clase_id,c.materia_id,c.estado,c.origen,c.lote_legado,c.registros_confirmados,
                TO_CHAR(c.fecha_hora,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') fecha_hora
                FROM clases c JOIN materias m ON m.materia_id=c.materia_id
                WHERE c.materia_id=:m AND m.profesor_id=:p ORDER BY c.fecha_hora DESC,c.clase_id DESC''',
                m=materia_id, p=profesor_id)
            return bd._filas_a_diccionarios(cur, cur.fetchall())
    return bd.ejecutar_con_reintentos(op)


def confirmar_clase(registros, profesor_id, clase_id, clave_confirmacion, origen):
    if not registros or len({r['materia_id'] for r in registros}) != 1:
        raise ValueError('La propuesta debe pertenecer a una única materia.')
    for r in registros:
        if type(r.get('presente')) is not bool:
            raise ValueError('Resuelve todas las decisiones pendientes antes de guardar.')
        desconocido = r.get('estado_deteccion') == 'SIN_MUESTRA'
        if (desconocido and r.get('presente_detectado') is not None) or (not desconocido and type(r.get('presente_detectado')) is not bool):
            raise ValueError('La detección y su estado no coinciden.')
        if r.get('estado_deteccion') == 'ANALISIS_FALLIDO':
            raise ValueError('Un análisis fallido no puede confirmar asistencia.')
    contenido = json.dumps([
        {'estudiante_id': r['estudiante_id'], 'detectado': None if r['presente_detectado'] is None else int(r['presente_detectado']),
         'estado_deteccion': r.get('estado_deteccion') or ('PRESENTE' if r['presente_detectado'] else 'AUSENTE'),
         'presente': int(r['presente']), 'motivo': r.get('motivo_correccion'),
         'fecha_hora': bd._fecha_hora_para_oracle(r['fecha_hora'])}
        for r in sorted(registros, key=lambda r: r['estudiante_id'])
    ], ensure_ascii=False, sort_keys=True, separators=(',', ':'))

    def op(conn):
        try:
            with conn.cursor() as cur:
                _comprobar_actor(cur, profesor_id)
                cur.execute('SELECT materia_id FROM clases WHERE clase_id=:c', c=clase_id)
                clase = cur.fetchone()
                if clase is None or clase[0] != registros[0]['materia_id']:
                    raise ValueError('La propuesta no corresponde a la clase seleccionada.')
                cantidad = cur.var(oracledb.NUMBER)
                cur.setinputsizes(carga=oracledb.DB_TYPE_CLOB)
                cur.execute('BEGIN pkg_clases.confirmar_clase(:c,:clave,:origen,:carga,:n); END;',
                            c=clase_id, clave=clave_confirmacion, origen=origen, carga=contenido, n=cantidad)
                total = int(cantidad.getvalue())
            conn.commit()
            return total
        except Exception:
            conn.rollback()
            raise
    try:
        return bd.ejecutar_con_reintentos(op, reintentos=1)
    except oracledb.Error as exc:
        _traducir_error(exc)
