"""Integracion Oracle 002: fixtures aislados por ID, sin COMMIT y con rollback final."""

import os
import unittest
from unittest.mock import patch
import uuid


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE') == '1', 'Requiere UPC_TEST_ORACLE=1 y migracion 002.')
class DisparadoresIntegracionTest(unittest.TestCase):
    def setUp(self):
        import oracledb
        from src.base_datos.configuracion import obtener_conexion, obtener_pool
        self.oracledb = oracledb
        self.pool = obtener_pool()
        self.conn = obtener_conexion()
        self.addCleanup(self.limpiar)
        self.tablas = ['profesores', 'estudiantes', 'materias', 'materia_estudiantes',
                       'registros_asistencia', 'auditoria_asistencia', 'historial_matriculas', 'clases',
                       'eventos_gestion', 'limites_acceso', 'administradores', 'sesiones_usuario', 'verificacion_estudiantes']
        with self.conn.cursor() as cur:
            cur.callproc('pkg_auditoria.limpiar_contexto')
            cur.execute("SELECT COUNT(*) FROM versiones_esquema WHERE version='002'")
            self.assertEqual(cur.fetchone()[0], 1, 'Aplicar la migracion 002 antes de las pruebas.')
            self.antes = self.contar_tablas()
            ids = [cur.var(oracledb.NUMBER) for _ in range(4)]
            codigo = 'TEST_' + uuid.uuid4().hex[:16]
            for sufijo, out in [('A', ids[0]), ('B', ids[1])]:
                cur.execute('INSERT INTO profesores (usuario,contrasena,nombre) VALUES (:u,:c,:n) RETURNING profesor_id INTO :id',
                            u=codigo+sufijo, c='FIXTURE_NO_ES_HASH', n='Fixture', id=out)
            self.profesor, self.otro_profesor = [int(v.getvalue()[0]) for v in ids[:2]]
            cur.execute('INSERT INTO estudiantes (nombre) VALUES (:n) RETURNING estudiante_id INTO :id', n='Fixture', id=ids[2])
            self.estudiante = int(ids[2].getvalue()[0])
            cur.execute('INSERT INTO materias (codigo_materia,nombre,profesor_id) VALUES (:c,:n,:p) RETURNING materia_id INTO :id',
                        c=codigo, n='Fixture', p=self.profesor, id=ids[3])
            self.materia = int(ids[3].getvalue()[0])

    def contar_tablas(self):
        with self.conn.cursor() as cur:
            resultado = []
            for tabla in self.tablas:
                cur.execute('SELECT COUNT(*) FROM ' + tabla)
                resultado.append(cur.fetchone()[0])
            return resultado

    def limpiar(self):
        try:
            self.conn.rollback()
            with self.conn.cursor() as cur:
                cur.callproc('pkg_auditoria.limpiar_contexto')
            if hasattr(self, 'antes'):
                self.assertEqual(self.contar_tablas(), self.antes, 'Las pruebas no deben dejar filas ni historial.')
        finally:
            self.pool.release(self.conn)

    def establecer(self, rol='PROFESOR', actor=None, motivo='Contexto de prueba'):
        if actor is None and rol == 'PROFESOR':
            actor = self.profesor
        with self.conn.cursor() as cur:
            cur.callproc('pkg_auditoria.establecer_contexto', [rol, actor, motivo])

    def preparar_asistencia(self):
        with self.conn.cursor() as cur:
            cur.callproc('pkg_asistencia.matricular_estudiante', [self.estudiante, self.materia])
            cur.execute('BEGIN pkg_asistencia.registrar_asistencia(:m,:e,SYSTIMESTAMP,0); END;',
                        m=self.materia, e=self.estudiante)
            cur.execute('SELECT asistencia_id FROM registros_asistencia WHERE materia_id=:m', m=self.materia)
            return int(cur.fetchone()[0])

    def esperar_error(self, codigo, nombre, parametros):
        with self.conn.cursor() as cur, self.assertRaises(self.oracledb.DatabaseError) as error:
            cur.callproc(nombre, parametros)
        self.assertEqual(error.exception.args[0].code, codigo)

    def test_correccion_baja_y_update_sin_cambios(self):
        self.establecer()
        sid = self.preparar_asistencia()
        with self.conn.cursor() as cur:
            motivo = 'Evidencia revisada: áéíóú ' + 'ñ' * 300
            cur.callproc('pkg_asistencia.corregir_asistencia', [sid, 1, motivo])
            cur.callproc('pkg_asistencia.corregir_asistencia', [sid, 1, 'Sin cambio real'])
            cur.execute('SELECT operacion,presente_anterior,presente_nuevo,actor_rol,actor_id,motivo FROM auditoria_asistencia WHERE asistencia_id=:s', s=sid)
            self.assertEqual(cur.fetchall(), [('UPDATE', 0, 1, 'PROFESOR', self.profesor, motivo)])
            self.assertEqual(cur.callfunc('pkg_auditoria.motivo_actual', str), 'Contexto de prueba')
            cur.callproc('pkg_asistencia.eliminar_asistencia', [sid, 'Registro duplicado'])
            cur.execute('SELECT operacion,presente_anterior,presente_nuevo FROM auditoria_asistencia WHERE asistencia_id=:s ORDER BY auditoria_id', s=sid)
            self.assertEqual(cur.fetchall(), [('UPDATE', 0, 1), ('DELETE', 1, None)])

    def test_sql_directo_sin_actor_y_cambio_de_fecha(self):
        sid = self.preparar_asistencia()
        with self.conn.cursor() as cur:
            cur.execute("UPDATE registros_asistencia SET fecha_hora=fecha_hora+INTERVAL '1' MINUTE WHERE asistencia_id=:s", s=sid)
            cur.execute('SELECT actor_rol,actor_id,usuario_bd,presente_anterior,presente_nuevo FROM auditoria_asistencia WHERE asistencia_id=:s', s=sid)
            fila = cur.fetchone()
            self.assertEqual((fila[0], fila[1], fila[3], fila[4]), ('NO_IDENTIFICADO', None, 0, 0))
            self.assertTrue(fila[2])

    def test_matricula_retiro_y_reinscripcion(self):
        self.establecer('ESTUDIANTE', self.estudiante, 'Inscripcion')
        with self.conn.cursor() as cur:
            cur.callproc('pkg_asistencia.matricular_estudiante', [self.estudiante, self.materia])
            cur.callproc('pkg_asistencia.retirar_estudiante', [self.estudiante, self.materia, 'Cambio de horario'])
            cur.callproc('pkg_asistencia.matricular_estudiante', [self.estudiante, self.materia])
            cur.execute('SELECT accion,actor_rol,actor_id FROM historial_matriculas WHERE materia_id=:m ORDER BY historial_id', m=self.materia)
            self.assertEqual(cur.fetchall(), [('ALTA', 'ESTUDIANTE', self.estudiante),
                                             ('RETIRO', 'ESTUDIANTE', self.estudiante),
                                             ('ALTA', 'ESTUDIANTE', self.estudiante)])

    def test_rollback_revierte_historial_pero_no_estado_de_paquete(self):
        self.establecer('SISTEMA', motivo='Rollback')
        with self.conn.cursor() as cur:
            cur.execute('SAVEPOINT cambios_test')
            sid = self.preparar_asistencia()
            cur.execute('UPDATE registros_asistencia SET presente=1 WHERE asistencia_id=:s', s=sid)
            cur.execute('ROLLBACK TO cambios_test')
            cur.execute('SELECT COUNT(*) FROM auditoria_asistencia WHERE asistencia_id=:s', s=sid)
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute('SELECT COUNT(*) FROM historial_matriculas WHERE materia_id=:m', m=self.materia)
            self.assertEqual(cur.fetchone()[0], 0)
            self.assertEqual(cur.callfunc('pkg_auditoria.rol_actual', str), 'SISTEMA')
            cur.callproc('pkg_auditoria.limpiar_contexto')
            self.assertEqual(cur.callfunc('pkg_auditoria.rol_actual', str), 'NO_IDENTIFICADO')

    def test_cascada_conserva_instantaneas(self):
        sid = self.preparar_asistencia()
        self.establecer('SISTEMA', motivo='Baja de materia')
        with self.conn.cursor() as cur:
            cur.execute('DELETE FROM materias WHERE materia_id=:m', m=self.materia)
            cur.execute('SELECT accion FROM historial_matriculas WHERE materia_id=:m ORDER BY historial_id', m=self.materia)
            self.assertEqual(cur.fetchall(), [('ALTA',), ('RETIRO',)])
            cur.execute('SELECT operacion,materia_anterior,presente_anterior FROM auditoria_asistencia WHERE asistencia_id=:s', s=sid)
            self.assertEqual(cur.fetchone(), ('DELETE', self.materia, 0))

    def test_fechas_de_actualizacion_impuestas_en_tres_tablas(self):
        for tabla, clave, valor in [('profesores', 'profesor_id', self.profesor),
                                    ('estudiantes', 'estudiante_id', self.estudiante),
                                    ('materias', 'materia_id', self.materia)]:
            with self.subTest(tabla=tabla), self.conn.cursor() as cur:
                cur.execute(f"UPDATE {tabla} SET actualizado_en=TIMESTAMP '2000-01-01 00:00:00' WHERE {clave}=:id", id=valor)
                cur.execute(f"SELECT CASE WHEN actualizado_en>=SYSTIMESTAMP-INTERVAL '1' MINUTE THEN 1 ELSE 0 END FROM {tabla} WHERE {clave}=:id", id=valor)
                self.assertEqual(cur.fetchone()[0], 1)

    def test_validaciones_de_contexto_propiedad_y_motivo(self):
        sid = self.preparar_asistencia()
        self.esperar_error(20031, 'pkg_asistencia.corregir_asistencia', [sid, 1, 'Prueba'])
        self.establecer(actor=self.otro_profesor)
        self.esperar_error(20032, 'pkg_asistencia.corregir_asistencia', [sid, 1, 'Prueba'])
        self.establecer()
        self.esperar_error(20030, 'pkg_asistencia.corregir_asistencia', [sid, 1, '  '])
        self.esperar_error(20030, 'pkg_asistencia.corregir_asistencia', [sid, 1, 'x' * 501])
        self.esperar_error(20011, 'pkg_asistencia.corregir_asistencia', [sid, 2, 'Prueba'])
        self.esperar_error(20033, 'pkg_asistencia.corregir_asistencia', [-1, 1, 'Prueba'])
        self.esperar_error(20061, 'pkg_auditoria.establecer_contexto', ['ADMIN', None, None])
        with self.conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM auditoria_asistencia WHERE asistencia_id=:s', s=sid)
            self.assertEqual(cur.fetchone()[0], 0)
            self.assertEqual(cur.callfunc('pkg_auditoria.motivo_actual', str), 'Contexto de prueba')

    def test_confirmacion_revalida_propiedad_y_matricula_sin_dejar_filas(self):
        from src.base_datos import bd
        conexion = self.conn

        class ConexionSinCommit:
            def cursor(self):
                return conexion.cursor()

            def commit(self):
                pass  # Se comprueba el INSERT y se revierte todo en limpiar().

        registros = [{'materia_id': self.materia, 'estudiante_id': self.estudiante,
                      'presente': True, 'fecha_hora': '2026-11-11T10:00:00.123456-05:00'}]
        self.establecer()
        with self.conn.cursor() as cur:
            cur.callproc('pkg_asistencia.matricular_estudiante', [self.estudiante, self.materia])
        with patch.object(bd, 'ejecutar_con_reintentos',
                          side_effect=lambda op, **kw: op(ConexionSinCommit())) as ejecutar:
            with self.assertRaises(PermissionError):
                bd.crear_asistencia(registros, profesor_id=self.otro_profesor)
            with self.assertRaises(ValueError):
                bd.crear_asistencia(registros * 2, profesor_id=self.profesor)
            with self.conn.cursor() as cur:
                cur.callproc('pkg_asistencia.retirar_estudiante',
                             [self.estudiante, self.materia, 'Prueba de matrícula modificada'])
            with self.assertRaisesRegex(ValueError, 'matrícula cambió'):
                bd.crear_asistencia(registros, profesor_id=self.profesor)
            with self.conn.cursor() as cur:
                cur.execute('SELECT COUNT(*) FROM registros_asistencia WHERE materia_id=:m', m=self.materia)
                self.assertEqual(cur.fetchone()[0], 0)
                cur.callproc('pkg_asistencia.matricular_estudiante', [self.estudiante, self.materia])
            self.assertEqual(bd.crear_asistencia(registros, profesor_id=self.profesor), 1)
            self.assertTrue(all(c.kwargs == {'reintentos': 1} for c in ejecutar.call_args_list))
        with self.conn.cursor() as cur:
            cur.execute('SELECT estudiante_id,presente FROM registros_asistencia WHERE materia_id=:m', m=self.materia)
            self.assertEqual(cur.fetchall(), [(self.estudiante, 1)])

    def test_contexto_de_python_se_limpia_al_reutilizar_y_al_fallar(self):
        from src.base_datos import bd
        with self.conn.cursor() as cur:
            cur.execute('SAVEPOINT fixture_contexto')

        class ConexionFixture:
            def cursor(_): return self.conn.cursor()
            def rollback(_):
                with self.conn.cursor() as cur: cur.execute('ROLLBACK TO fixture_contexto')

        conexion_fixture = ConexionFixture()

        class PoolSinCerrar:
            def release(_, conexion):
                self.assertIs(conexion, conexion_fixture)

            def drop(_, conexion):
                self.fail('No debe fallar la limpieza del contexto.')

        def leer_rol(conn):
            with conn.cursor() as cur:
                return cur.callfunc('pkg_auditoria.rol_actual', str)

        def fallar(conn):
            self.assertEqual(leer_rol(conn), 'PROFESOR')
            raise ValueError('Fallo controlado')

        with patch.object(bd, 'obtener_conexion', return_value=conexion_fixture), patch.object(bd, 'obtener_pool', return_value=PoolSinCerrar()):
            with patch.object(bd, '_contexto_auditoria_actual', return_value=('PROFESOR', self.profesor, None)), patch('src.utilidades.sesiones._actor_local',return_value=('profesor',self.profesor,'fixture-token-seguro')), patch('src.servicios.sesiones_servidor.validar_en_conexion'):
                self.assertEqual(bd.ejecutar_con_reintentos(leer_rol), 'PROFESOR')
                self.assertEqual(leer_rol(self.conn), 'NO_IDENTIFICADO')
                with self.assertRaisesRegex(ValueError, 'Fallo controlado'):
                    bd.ejecutar_con_reintentos(fallar)
                self.assertEqual(leer_rol(self.conn), 'NO_IDENTIFICADO')
            self.establecer('ESTUDIANTE', self.estudiante)
            with patch.object(bd, '_contexto_auditoria_actual', return_value=None):
                self.assertEqual(bd.ejecutar_con_reintentos(leer_rol), 'NO_IDENTIFICADO')


if __name__ == '__main__':
    unittest.main()
