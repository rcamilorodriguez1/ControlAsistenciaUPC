import os
import unittest
from unittest.mock import patch

import numpy as np

import test_disparadores_integracion as fixtures


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE') == '1', 'Requiere Oracle local y UPC_TEST_ORACLE=1.')
class MuestrasOracleTest(unittest.TestCase):
    setUp = fixtures.DisparadoresIntegracionTest.setUp
    limpiar = fixtures.DisparadoresIntegracionTest.limpiar
    contar_tablas = fixtures.DisparadoresIntegracionTest.contar_tablas

    def test_alta_guarda_solo_descriptores_validos_y_voz_normalizada(self):
        from src.base_datos import bd
        conexion = self.conn

        class SinCommit:
            def cursor(self): return conexion.cursor()
            def commit(self): pass

        with patch.object(bd, 'ejecutar_con_reintentos', side_effect=lambda op, **kw: op(SinCommit())):
            respuesta = bd.crear_estudiante('Fixture de biometría', [0.1] * 128, [2.] * 256, codigo_institucional='TEST-BIOMETRIA')
        with self.conn.cursor() as cur:
            cur.execute('SELECT embedding_facial,embedding_voz FROM estudiantes WHERE estudiante_id=:e', e=respuesta[0]['estudiante_id'])
            facial, voz = (bd._deserializar_embedding(v) for v in cur.fetchone())
        np.testing.assert_allclose(facial, [0.1] * 128)
        self.assertEqual(len(voz), 256)
        self.assertAlmostEqual(np.linalg.norm(voz), 1.)
