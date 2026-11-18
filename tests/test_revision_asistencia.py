import unittest
from unittest.mock import patch

from src.servicios.asistencia import confirmar_resultado
from src.servicios.revision import preparar_revision
from src.utilidades.sesiones import iniciar_sesion, preparar_toma, guardar_resultado, obtener_resultado


class RevisionAsistenciaTest(unittest.TestCase):
    def setUp(self):
        self.registros = [{'estudiante_id': 7, 'materia_id': 10, 'presente': False,
                           'fecha_hora': '2026-11-11T10:00:00-05:00'}]
        self.estado = {}
        iniciar_sesion('profesor', {'profesor_id': 1, 'usuario': 'p', 'nombre': 'P'}, self.estado)
        self.contexto = preparar_toma(10, self.estado, clase_id=100)
        self.rid = guardar_resultado(self.contexto, [{'Nombre': 'Alumno'}], self.registros, 'facial', self.estado)

    def test_correccion_conserva_deteccion_y_envia_motivo_profesor_y_clase(self):
        revision = [{'ID': 7, 'Presente': True, 'Motivo': '  Verificado en el salón  '}]
        with patch('src.servicios.asistencia.crear_asistencia', return_value=1) as guardar:
            confirmar_resultado(self.rid, self.estado, revision=revision)
            registro = guardar.call_args.args[0][0]
            self.assertFalse(registro['presente_detectado'])
            self.assertTrue(registro['presente'])
            self.assertEqual(registro['motivo_correccion'], 'Verificado en el salón')
            self.assertEqual(guardar.call_args.kwargs, {'profesor_id': 1, 'clase_id': 100,
                                                       'clave_confirmacion': self.rid, 'origen': 'facial'})

    def test_revision_invalida_no_consume_propuesta_ni_escribe(self):
        for revision in [[], [{'ID': 8, 'Presente': True}], [{'ID': 7, 'Presente': 'sí'}],
                         [{'ID': 7, 'Presente': True, 'Motivo': ''}],
                         [{'ID': 7, 'Presente': True, 'Motivo': 'x' * 501}],
                         [{'ID': 7, 'Presente': False}] * 2]:
            with self.subTest(revision=revision), patch('src.servicios.asistencia.crear_asistencia') as guardar:
                with self.assertRaises(ValueError):
                    confirmar_resultado(self.rid, self.estado, revision=revision)
                self.assertIsNotNone(obtener_resultado(self.rid, self.estado))
                guardar.assert_not_called()

    def test_cambio_de_clase_invalida_capturas_y_confirmacion(self):
        self.estado['imagenes_asistencia'] = ['foto']
        preparar_toma(10, self.estado, clase_id=101)
        with patch('src.servicios.asistencia.crear_asistencia') as guardar:
            with self.assertRaises(PermissionError):
                confirmar_resultado(self.rid, self.estado)
            guardar.assert_not_called()
        self.assertEqual(self.estado['imagenes_asistencia'], [])

    def test_sin_clase_no_se_genera_propuesta(self):
        contexto = preparar_toma(10, self.estado)
        with self.assertRaises(ValueError):
            guardar_resultado(contexto, [{'Nombre': 'Alumno'}], self.registros, 'facial', self.estado)

    def test_sin_cambio_se_conserva_deteccion_y_no_se_inventa_revision(self):
        revisados = preparar_revision(self.registros, [{'ID': 7, 'Presente': False, 'Motivo': 'sin cambio'}])
        self.assertIsNone(revisados[0]['motivo_correccion'])
        self.assertFalse(revisados[0]['presente_detectado'])
        self.assertNotIn('presente_detectado', self.registros[0])
