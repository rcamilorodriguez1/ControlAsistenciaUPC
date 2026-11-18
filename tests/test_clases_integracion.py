"""Clases 003: procedimientos reales y concurrencia de conexiones Oracle."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from threading import Barrier
import unittest
from unittest.mock import patch
from uuid import uuid4

import test_disparadores_integracion as fixtures


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE') == '1', 'Requiere UPC_TEST_ORACLE=1 y migracion 003.')
class ClasesIntegracionTest(unittest.TestCase):
    limpiar = fixtures.DisparadoresIntegracionTest.limpiar
    contar_tablas = fixtures.DisparadoresIntegracionTest.contar_tablas
    establecer = fixtures.DisparadoresIntegracionTest.establecer
    esperar_error = fixtures.DisparadoresIntegracionTest.esperar_error

    def setUp(self):
        fixtures.DisparadoresIntegracionTest.setUp(self)
        self.establecer()
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM versiones_esquema WHERE version='003'")
            self.assertEqual(cur.fetchone()[0], 1)
            cur.callproc('pkg_asistencia.matricular_estudiante', [self.estudiante, self.materia])

    def abrir(self, fecha='2026-11-11T08:00:00.000000-05:00'):
        with self.conn.cursor() as cur:
            salida = cur.var(self.oracledb.NUMBER)
            cur.execute('''BEGIN pkg_clases.abrir_clase(:m,
                TO_TIMESTAMP_TZ(:f,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM'),:id); END;''',
                m=self.materia, f=fecha, id=salida)
            return int(salida.getvalue())

    def carga(self, **cambios):
        return json.dumps([{'estudiante_id': self.estudiante, 'detectado': 0, 'presente': 1,
                           'motivo': 'Revisión de evidencia en el salón',
                           'fecha_hora': '2026-11-11T08:15:00.123456-05:00', **cambios}], ensure_ascii=False)

    def confirmar(self, clase, carga, clave=None, conn=None):
        with (conn or self.conn).cursor() as cur:
            salida = cur.var(self.oracledb.NUMBER)
            cur.setinputsizes(carga=self.oracledb.DB_TYPE_CLOB)
            cur.execute('BEGIN pkg_clases.confirmar_clase(:c,:k,:o,:carga,:n); END;',
                        c=clase, k=clave or uuid4().hex, o='FACIAL', carga=carga, n=salida)
            return int(salida.getvalue())

    def test_mismo_instante_con_otro_offset_abre_la_misma_clase(self):
        clase = self.abrir()
        self.assertEqual(self.abrir('2026-11-11T13:00:00.000000+00:00'), clase)
        self.assertNotEqual(self.abrir('2026-11-11T09:00:00.000000-05:00'), clase)
        self.establecer(actor=self.otro_profesor)
        with self.assertRaises(self.oracledb.DatabaseError) as error:
            self.abrir()
        self.assertEqual(error.exception.args[0].code, 20072)

    def test_revision_se_guarda_y_reintento_no_duplica_ni_sobrescribe(self):
        clase, clave, carga = self.abrir(), uuid4().hex, self.carga()
        self.assertEqual(self.confirmar(clase, carga, clave), 1)
        self.assertEqual(self.confirmar(clase, carga, clave), 1)
        for k, contenido in [(uuid4().hex, carga), (clave, self.carga(presente=0, motivo=None))]:
            with self.assertRaises(self.oracledb.DatabaseError) as error:
                self.confirmar(clase, contenido, k)
            self.assertEqual(error.exception.args[0].code, 20074)
        with self.conn.cursor() as cur:
            cur.execute('SELECT presente_detectado,presente,corregido_manual,motivo_correccion,revisado_por FROM registros_asistencia WHERE clase_id=:c', c=clase)
            self.assertEqual(cur.fetchall(), [(0, 1, 1, 'Revisión de evidencia en el salón', self.profesor)])
            cur.execute('SELECT estado,origen,registros_confirmados FROM clases WHERE clase_id=:c', c=clase)
            self.assertEqual(cur.fetchone(), ('CONFIRMADA', 'FACIAL', 1))
            for sentencia in ["UPDATE clases SET estado='BORRADOR' WHERE clase_id=:c",
                              'UPDATE clases SET registros_confirmados=99 WHERE clase_id=:c',
                              'UPDATE clases SET propuesta_confirmada=NULL WHERE clase_id=:c']:
                with self.assertRaises(self.oracledb.DatabaseError) as error:
                    cur.execute(sentencia, c=clase)
                self.assertEqual(error.exception.args[0].code, 20079)
            with self.assertRaises(self.oracledb.DatabaseError) as error:
                cur.execute('''INSERT INTO registros_asistencia(clase_id,materia_id,estudiante_id,fecha_hora,presente)
                    VALUES(:c,:m,:e,SYSTIMESTAMP,1)''', c=clase, m=self.materia, e=self.estudiante)
            self.assertEqual(error.exception.args[0].code, 20074)
            cur.execute('SELECT asistencia_id FROM registros_asistencia WHERE clase_id=:c', c=clase)
            aid = cur.fetchone()[0]
            cur.callproc('pkg_asistencia.eliminar_asistencia', [aid, 'Verificar instantánea de revisión inicial'])
            cur.execute('SELECT clase_anterior,detectado_anterior,correccion_inicial,motivo_inicial,revisor_inicial FROM auditoria_asistencia WHERE asistencia_id=:a', a=aid)
            self.assertEqual(cur.fetchone(), (clase, 0, 1, 'Revisión de evidencia en el salón', self.profesor))
            cur.execute('SELECT registros,tomas_registradas FROM v_resumen_materias WHERE materia_id=:m', m=self.materia)
            self.assertEqual(cur.fetchone(), (0, 1), 'Borrar una fila no borra la clase confirmada del resumen.')

    def test_error_en_segunda_fila_revierte_toda_la_confirmacion(self):
        clase = self.abrir()
        with self.conn.cursor() as cur:
            salida = cur.var(self.oracledb.NUMBER)
            cur.execute('INSERT INTO estudiantes(nombre) VALUES(:n) RETURNING estudiante_id INTO :id', n='Fixture segundo alumno', id=salida)
            segundo = int(salida.getvalue()[0])
            cur.callproc('pkg_asistencia.matricular_estudiante', [segundo, self.materia])
        carga = json.loads(self.carga())
        carga.append({**carga[0], 'estudiante_id': segundo, 'motivo': None})
        with self.assertRaises(self.oracledb.DatabaseError) as error:
            self.confirmar(clase, json.dumps(carga))
        self.assertEqual(error.exception.args[0].code, 20078)
        with self.conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM registros_asistencia WHERE clase_id=:c', c=clase)
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute('SELECT estado FROM clases WHERE clase_id=:c', c=clase)
            self.assertEqual(cur.fetchone()[0], 'BORRADOR')

    def test_matricula_modificada_y_otra_transaccion_de_matricula_se_rechazan(self):
        clase = self.abrir()
        otra = self.pool.acquire()
        try:
            with otra.cursor() as cur:
                cur.execute('LOCK TABLE materia_estudiantes IN ROW EXCLUSIVE MODE NOWAIT')
            with self.assertRaises(self.oracledb.DatabaseError) as error:
                self.confirmar(clase, self.carga())
            self.assertEqual(error.exception.args[0].code, 20075)
        finally:
            otra.rollback()
            self.pool.release(otra)
        with self.conn.cursor() as cur:
            cur.callproc('pkg_asistencia.retirar_estudiante', [self.estudiante, self.materia, 'Prueba'])
        with self.assertRaises(self.oracledb.DatabaseError) as error:
            self.confirmar(clase, self.carga())
        self.assertEqual(error.exception.args[0].code, 20076)

    def test_api_python_usa_plsql_y_reportes_agrupan_por_clase(self):
        from src.base_datos import bd
        from src.base_datos.clases import abrir_clase
        conexion = self.conn

        class SinCommit:
            def cursor(self): return conexion.cursor()
            def commit(self): pass
            def rollback(self): conexion.rollback()

        with patch.object(bd, 'ejecutar_con_reintentos', side_effect=lambda op, **kw: op(SinCommit())):
            clase = abrir_clase(self.materia, self.profesor, '2026-11-11T08:00:00-05:00')
            registros = [{'materia_id': self.materia, 'estudiante_id': self.estudiante,
                          'fecha_hora': '2026-11-11T08:15:00.123456-05:00', 'presente': True,
                          'presente_detectado': False, 'motivo_correccion': 'Revisión'}]
            self.assertEqual(bd.crear_asistencia(registros, profesor_id=self.profesor, clase_id=clase,
                                                clave_confirmacion=uuid4().hex, origen='voz'), 1)
            reporte = bd.obtener_asistencia_profesor(self.profesor)
            self.assertEqual(reporte[0]['clase_id'], clase)
            self.assertEqual(reporte[0]['fecha_clase'], '2026-11-11T08:00:00.000000-05:00')
            self.assertEqual(bd.obtener_materias_profesor(self.profesor)[0]['total_clases'], 1)

    def test_dos_conexiones_confirman_sin_duplicar_ni_con_propuestas_distintas(self):
        # Unica prueba que confirma fixtures para hacerlos visibles a dos conexiones.
        # Limpieza por IDs exclusivos antes del rollback/comprobacion general del setUp.
        def limpiar_confirmados():
            self.conn.rollback()
            with self.conn.cursor() as cur:
                cur.execute('DELETE FROM profesores WHERE profesor_id IN (:a,:b)', a=self.profesor, b=self.otro_profesor)
                cur.execute('DELETE FROM estudiantes WHERE estudiante_id=:e', e=self.estudiante)
                cur.execute('DELETE FROM auditoria_asistencia WHERE materia_anterior=:m OR materia_nueva=:m', m=self.materia)
                cur.execute('DELETE FROM historial_matriculas WHERE materia_id=:m', m=self.materia)
            self.conn.commit()
        self.addCleanup(limpiar_confirmados)
        for indice, misma_clave in enumerate((True, False)):
            clase = self.abrir(f'2026-11-11T{8+indice:02}:00:00.000000-05:00')
            self.conn.commit()
            barrera, clave, carga = Barrier(2), uuid4().hex, self.carga()

            def cliente(numero):
                conn = self.pool.acquire()
                conn.call_timeout = 10000
                try:
                    with conn.cursor() as cur:
                        cur.callproc('pkg_auditoria.establecer_contexto', ['PROFESOR', self.profesor, None])
                    barrera.wait(timeout=10)
                    try:
                        cantidad = self.confirmar(clase, carga, clave if misma_clave else uuid4().hex, conn)
                        conn.commit()
                        return ('ok', cantidad)
                    except self.oracledb.DatabaseError as exc:
                        conn.rollback()
                        return ('error', exc.args[0].code)
                finally:
                    conn.rollback()
                    with conn.cursor() as cur: cur.callproc('pkg_auditoria.limpiar_contexto')
                    conn.call_timeout = 0
                    self.pool.release(conn)

            with ThreadPoolExecutor(max_workers=2) as ejecutor:
                resultados = list(ejecutor.map(cliente, (1, 2)))
            self.assertEqual(sorted(resultados), [('ok', 1), ('ok', 1)] if misma_clave else [('error', 20074), ('ok', 1)])
            with self.conn.cursor() as cur:
                cur.execute('SELECT COUNT(*) FROM registros_asistencia WHERE clase_id=:c', c=clase)
                self.assertEqual(cur.fetchone()[0], 1)

    def test_restriccion_unica_tambien_impide_duplicados_en_sql_legado(self):
        with self.conn.cursor() as cur:
            cur.execute('''INSERT INTO registros_asistencia(materia_id,estudiante_id,fecha_hora,presente)
                VALUES(:m,:e,TIMESTAMP '2026-11-11 08:00:00 -05:00',1)''', m=self.materia, e=self.estudiante)
            with self.assertRaises(self.oracledb.IntegrityError) as error:
                cur.execute('''INSERT INTO registros_asistencia(materia_id,estudiante_id,fecha_hora,presente)
                    VALUES(:m,:e,TIMESTAMP '2026-11-11 08:00:00 -05:00',0)''', m=self.materia, e=self.estudiante)
            self.assertEqual(error.exception.args[0].code, 1)

    def test_confirmar_exige_profesor_propietario_incluso_al_reintentar(self):
        clase = self.abrir()
        for rol, actor, codigo in [('ESTUDIANTE', self.estudiante, 20071),
                                    ('PROFESOR', self.otro_profesor, 20072)]:
            self.establecer(rol, actor)
            with self.assertRaises(self.oracledb.DatabaseError) as error:
                self.confirmar(clase, self.carga())
            self.assertEqual(error.exception.args[0].code, codigo)
        self.establecer()

    def test_agrupacion_historica_conserva_duplicados_y_microsegundos(self):
        # Datos sinteticos de solo lectura: offsets equivalentes, duplicados y otra materia.
        with self.conn.cursor() as cur:
            cur.execute('''WITH historico(a,m,e,f) AS (
                SELECT 1,10,7,TIMESTAMP '2026-11-11 08:00:00.000000 -05:00' FROM dual UNION ALL
                SELECT 2,10,7,TIMESTAMP '2026-11-11 13:00:00.000000 +00:00' FROM dual UNION ALL
                SELECT 3,10,8,TIMESTAMP '2026-11-11 08:00:00.000000 -05:00' FROM dual UNION ALL
                SELECT 4,20,7,TIMESTAMP '2026-11-11 08:00:00.000000 -05:00' FROM dual UNION ALL
                SELECT 5,10,7,TIMESTAMP '2026-11-11 08:00:00.000001 -05:00' FROM dual)
                SELECT a,m,e,SYS_EXTRACT_UTC(f),
                    ROW_NUMBER() OVER(PARTITION BY m,SYS_EXTRACT_UTC(f),e ORDER BY a)-1 lote
                FROM historico ORDER BY a''')
            filas = cur.fetchall()
        self.assertEqual([r[4] for r in filas], [0, 1, 0, 0, 0])
        clases = {(r[1], r[3], r[4]) for r in filas}
        self.assertEqual(len(filas), 5)
        self.assertEqual(len(clases), 4)
        self.assertEqual(len({(r[1], r[3], r[4], r[2]) for r in filas}), 5)

    def test_sin_muestra_necesita_motivo_y_conserva_deteccion_null(self):
        clase = self.abrir()
        carga = self.carga(detectado=None, estado_deteccion='SIN_MUESTRA', presente=0, motivo=None)
        with self.assertRaises(self.oracledb.DatabaseError) as error:
            self.confirmar(clase, carga)
        self.assertEqual(error.exception.args[0].code, 20078)
        self.assertEqual(self.confirmar(clase, self.carga(detectado=None, estado_deteccion='SIN_MUESTRA',
                         presente=0, motivo='Lista comprobada manualmente')), 1)
        with self.conn.cursor() as cur:
            cur.execute('''SELECT presente_detectado,presente,estado_deteccion,corregido_manual,revisado_por
                FROM registros_asistencia WHERE clase_id=:c''', c=clase)
            self.assertEqual(cur.fetchone(), (None, 0, 'SIN_MUESTRA', 1, self.profesor))
            with self.assertRaises(self.oracledb.DatabaseError) as error:
                cur.execute('UPDATE registros_asistencia SET presente_detectado=0 WHERE clase_id=:c', c=clase)
            self.assertEqual(error.exception.args[0].code, 20079)
            cur.execute('DELETE FROM registros_asistencia WHERE clase_id=:c', c=clase)
            cur.execute('SELECT detectado_anterior,estado_anterior FROM auditoria_asistencia WHERE clase_anterior=:c', c=clase)
            self.assertEqual(cur.fetchone(), (None, 'SIN_MUESTRA'))

    def test_oracle_rechaza_fallo_pendiente_y_estados_incoherentes(self):
        clase = self.abrir()
        for cambios in [dict(detectado=None, estado_deteccion='ANALISIS_FALLIDO'),
                        dict(detectado=None, estado_deteccion='SIN_MUESTRA', presente=None),
                        dict(detectado=None, estado_deteccion='PRESENTE'),
                        dict(detectado=0, estado_deteccion='SIN_MUESTRA'), dict(detectado=None)]:
            with self.subTest(cambios=cambios), self.assertRaises(self.oracledb.DatabaseError) as error:
                self.confirmar(clase, self.carga(**cambios))
            self.assertEqual(error.exception.args[0].code, 20077)
        with self.conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM registros_asistencia WHERE clase_id=:c', c=clase)
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute('SELECT estado FROM clases WHERE clase_id=:c', c=clase)
            self.assertEqual(cur.fetchone()[0], 'BORRADOR')

    def test_sql_directo_tampoco_puede_disfrazar_sin_muestra_como_ausencia_automatica(self):
        clase = self.abrir()
        with self.conn.cursor() as cur, self.assertRaises(self.oracledb.IntegrityError) as error:
            cur.execute('''INSERT INTO registros_asistencia(clase_id,materia_id,estudiante_id,fecha_hora,
                presente,presente_detectado,estado_deteccion,corregido_manual)
                VALUES(:c,:m,:e,SYSTIMESTAMP,0,NULL,'SIN_MUESTRA',0)''',
                c=clase, m=self.materia, e=self.estudiante)
        self.assertEqual(error.exception.args[0].code, 2290)
