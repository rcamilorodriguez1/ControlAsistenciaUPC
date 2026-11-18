"""Prueba transaccional opt-in: usa el esquema local y revierte todos sus datos de prueba."""

import os
import unittest
from unittest.mock import patch
import uuid


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE') == '1', 'Definir UPC_TEST_ORACLE=1 para probar Oracle real con rollback.')
class OracleIntegracionTest(unittest.TestCase):
    def test_flujo_plsql_y_fechas_independientes_de_la_zona_de_sesion(self):
        import oracledb
        from src.base_datos import bd
        from src.base_datos.configuracion import obtener_conexion, obtener_pool
        from src.utilidades.fecha_hora import convertir_a_hora_colombia

        conn = obtener_conexion()

        class ConexionSinCommit:
            def cursor(self):
                return conn.cursor()

            def commit(self):
                pass  # El caso entero termina en rollback, incluidas llamadas de bd.py.

        tablas = ['profesores', 'estudiantes', 'materias', 'materia_estudiantes', 'registros_asistencia', 'clases']
        anteriores = []
        zona_anterior = '-05:00'
        try:
            with conn.cursor() as cur:
                for tabla in tablas:
                    cur.execute('SELECT COUNT(*) FROM ' + tabla)
                    anteriores.append(cur.fetchone()[0])
                cur.execute('SELECT sessiontimezone FROM dual')
                zona_anterior = cur.fetchone()[0]
                cur.execute("ALTER SESSION SET TIME_ZONE = '+09:00'")
                profesor, estudiante, materia = [cur.var(oracledb.NUMBER) for _ in range(3)]
                codigo = 'TEST_' + uuid.uuid4().hex[:12]
                cur.execute('INSERT INTO profesores (usuario, contrasena, nombre) VALUES (:u, :c, :n) RETURNING profesor_id INTO :id',
                            u=codigo, c='hash_de_prueba_no_utilizable', n='Fixture transaccional', id=profesor)
                cur.execute('INSERT INTO estudiantes (nombre) VALUES (:n) RETURNING estudiante_id INTO :id',
                            n='Fixture transaccional', id=estudiante)
                pid, eid = int(profesor.getvalue()[0]), int(estudiante.getvalue()[0])
                cur.execute('INSERT INTO materias (codigo_materia, nombre, profesor_id) VALUES (:c, :n, :p) RETURNING materia_id INTO :id',
                            c=codigo, n='Fixture transaccional', p=pid, id=materia)
                mid = int(materia.getvalue()[0])
                with self.assertRaises(oracledb.DatabaseError) as error:
                    cur.execute("BEGIN pkg_asistencia.registrar_asistencia(:m, :e, SYSTIMESTAMP, 1); END;", m=mid, e=eid)
                self.assertEqual(error.exception.args[0].code, 20012)
                cur.callproc('pkg_asistencia.matricular_estudiante', [eid, mid])
                with self.assertRaises(oracledb.DatabaseError) as error:
                    cur.callproc('pkg_asistencia.matricular_estudiante', [eid, mid])
                self.assertEqual(error.exception.args[0].code, 20010)
                fecha = '2026-11-08T10:15:30.123456-05:00'
                with patch.object(bd, 'ejecutar_con_reintentos', lambda op, **kw: op(ConexionSinCommit())):
                    self.assertEqual(bd.crear_asistencia([{'materia_id': mid, 'estudiante_id': eid,
                                                         'fecha_hora': fecha, 'presente': True}]), 1)
                    registros = bd.obtener_asistencia_estudiante(eid)
                    self.assertEqual(registros[0]['fecha_hora'], fecha)
                    docente = bd.obtener_asistencia_profesor(pid)
                    self.assertEqual(docente[0]['fecha_hora'], fecha)
                    self.assertEqual(convertir_a_hora_colombia(registros[0]['fecha_hora']).hour, 10)
                self.assertEqual(cur.callfunc('pkg_asistencia.porcentaje_asistencia', oracledb.NUMBER, [eid, mid]), 100)
        finally:
            conn.rollback()
            with conn.cursor() as cur:
                cur.execute("ALTER SESSION SET TIME_ZONE = '" + zona_anterior.replace("'", "''") + "'")
                posteriores = []
                for tabla in tablas:
                    cur.execute('SELECT COUNT(*) FROM ' + tabla)
                    posteriores.append(cur.fetchone()[0])
            obtener_pool().release(conn)
        self.assertEqual(posteriores, anteriores, 'No deben quedar filas de prueba.')


if __name__ == '__main__':
    unittest.main()
