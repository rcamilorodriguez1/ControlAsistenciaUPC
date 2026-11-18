"""Lectura real e aislamiento en Oracle 007; datos propios sin COMMIT, rollback final."""
import os
import unittest
from unittest.mock import patch

import test_disparadores_integracion as fixtures
from src.base_datos.perfil_estudiante import consultar_datos
from src.servicios.perfil_estudiante import construir_perfil


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE') == '1', 'Requiere Oracle 007.')
class PerfilOracleTest(unittest.TestCase):
    limpiar = fixtures.DisparadoresIntegracionTest.limpiar
    contar_tablas = fixtures.DisparadoresIntegracionTest.contar_tablas
    establecer = fixtures.DisparadoresIntegracionTest.establecer

    def setUp(self):
        fixtures.DisparadoresIntegracionTest.setUp(self)
        p = patch('src.base_datos.perfil_estudiante.bd.ejecutar_con_reintentos', side_effect=lambda operacion: operacion(self.conn))
        p.start(); self.addCleanup(p.stop)

    def test_perfil_sin_materias_y_con_matricula_sin_clases(self):
        self.establecer('ESTUDIANTE', self.estudiante)
        perfil = construir_perfil(consultar_datos(self.estudiante))
        self.assertEqual(perfil['total_materias'], 0)
        self.assertIsNone(perfil['porcentaje'])
        with self.conn.cursor() as cur:
            cur.callproc('pkg_asistencia.matricular_estudiante', [self.estudiante, self.materia])
        perfil = construir_perfil(consultar_datos(self.estudiante))
        self.assertEqual(perfil['total_materias'], 1)
        self.assertEqual(perfil['total'], 0)

    def test_decisiones_confirmadas_e_historia_tras_retiro_sin_filtrar_otro_estudiante(self):
        self.establecer()
        with self.conn.cursor() as cur:
            cur.callproc('pkg_asistencia.matricular_estudiante', [self.estudiante, self.materia])
            cur.execute("BEGIN pkg_asistencia.registrar_asistencia(:m,:e,SYSTIMESTAMP-INTERVAL '1' DAY,1); END;", m=self.materia, e=self.estudiante)
            cur.execute("BEGIN pkg_asistencia.registrar_asistencia(:m,:e,SYSTIMESTAMP,0); END;", m=self.materia, e=self.estudiante)
            salida = cur.var(self.oracledb.NUMBER)
            cur.execute("INSERT INTO estudiantes(nombre) VALUES('Otro fixture perfil') RETURNING estudiante_id INTO :s", s=salida)
            otro = int(salida.getvalue()[0])
            cur.callproc('pkg_asistencia.matricular_estudiante', [otro, self.materia])
            cur.execute("BEGIN pkg_asistencia.registrar_asistencia(:m,:e,SYSTIMESTAMP,1); END;", m=self.materia, e=otro)
        self.establecer('ESTUDIANTE', self.estudiante)
        filas = consultar_datos(self.estudiante)
        self.assertTrue(all(f['estudiante_id'] == self.estudiante for f in filas))
        perfil = construir_perfil(filas)
        self.assertEqual((perfil['asistidas'], perfil['ausencias'], perfil['porcentaje']), (1, 1, 50))
        with self.conn.cursor() as cur:
            cur.callproc('pkg_asistencia.retirar_estudiante', [self.estudiante, self.materia, 'Retiro de fixture de perfil'])
        perfil = construir_perfil(consultar_datos(self.estudiante))
        self.assertEqual(perfil['total_materias'], 0)
        self.assertEqual(perfil['total'], 2)

    def test_oracle_rechaza_rol_docente_y_id_ajeno(self):
        self.establecer()
        with self.assertRaises(PermissionError): consultar_datos(self.estudiante)
        self.establecer('ESTUDIANTE', self.estudiante)
        with self.assertRaises(PermissionError): consultar_datos(self.estudiante + 999999)
