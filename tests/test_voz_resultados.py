import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from src.canalizaciones import canalizacion_voz as voz
from src.servicios.resultados_voz import construir_resultados_voz
from src.servicios.revision import preparar_revision


class AnalisisVozTest(unittest.TestCase):
    def setUp(self):
        self.encoder = MagicMock()
        self.eje0 = np.eye(256)[0]
        self.eje1 = np.eye(256)[1]
        self.encoder.embed_utterance.return_value = self.eje0
        self.parches = [patch.object(voz, 'cargar_codificador_voz', return_value=self.encoder),
                        patch.object(voz, 'cargar_audio_seguro', return_value=np.ones(16000)),
                        patch.object(voz.librosa.effects, 'split', return_value=np.array([[0, 16000]])),
                        patch.object(voz, 'preprocess_wav', side_effect=lambda a: a),
                        patch.object(voz, 'validar_tramo_voz', side_effect=lambda a, **kw: a)]
        self.mock = [p.start() for p in self.parches]
        for p in self.parches: self.addCleanup(p.stop)
        self.candidatos = {7: self.eje0.tolist(), 8: self.eje1.tolist()}

    def test_excepcion_en_cualquier_etapa_es_fallo_sin_ausencias(self):
        for indice in range(4):
            with self.subTest(etapa=indice):
                self.mock[indice].side_effect = RuntimeError('fallo simulado')
                with self.assertLogs(voz._logger, level='ERROR'):
                    resultado = voz.procesar_audio_masivo(b'audio', self.candidatos)
                self.assertEqual(resultado.estado, 'FALLIDO')
                self.assertEqual(resultado.puntajes, {})
                self.mock[indice].side_effect = (lambda a: a) if indice == 3 else None

    def test_fallo_tras_una_coincidencia_descarta_el_resultado_parcial(self):
        self.mock[2].return_value = np.array([[0, 8000], [8000, 16000]])
        self.encoder.embed_utterance.side_effect = [self.eje0, RuntimeError('fallo')]
        with self.assertLogs(voz._logger, level='ERROR'):
            resultado = voz.procesar_audio_masivo(b'audio', self.candidatos)
        self.assertEqual((resultado.estado, resultado.puntajes), ('FALLIDO', {}))

    def test_analisis_completo_sin_coincidencias_es_distinto_de_fallo(self):
        self.encoder.embed_utterance.return_value = -self.eje0
        resultado = voz.procesar_audio_masivo(b'audio', self.candidatos)
        self.assertEqual((resultado.estado, resultado.puntajes), ('COMPLETADO', {}))

    def test_audio_vacio_silencio_y_segmentos_descartados_no_son_negativos(self):
        self.assertEqual(voz.procesar_audio_masivo(b'', self.candidatos).estado, 'FALLIDO')
        self.mock[1].return_value = np.zeros(16000)
        self.assertEqual(voz.procesar_audio_masivo(b'audio', self.candidatos).estado, 'FALLIDO')
        self.mock[1].return_value = np.ones(16000)
        self.mock[2].return_value = np.array([[0, 100]])
        self.assertEqual(voz.procesar_audio_masivo(b'audio', self.candidatos).estado, 'FALLIDO')
        self.encoder.embed_utterance.assert_not_called()

    def test_sin_candidatos_no_ejecuta_el_modelo(self):
        self.assertEqual(voz.procesar_audio_masivo(b'audio', {}).estado, 'SIN_MUESTRAS')
        self.mock[0].assert_not_called()

    def test_vectores_no_finitos_no_producen_ausencias(self):
        resultado = voz.procesar_audio_masivo(b'audio', {7: [np.nan] + [0.] * 255})
        self.assertEqual(resultado.estado, 'FALLIDO')
        self.encoder.embed_utterance.return_value = np.array([np.nan] + [0.] * 255)
        self.assertEqual(voz.procesar_audio_masivo(b'audio', self.candidatos).estado, 'FALLIDO')


class EstadosVozTest(unittest.TestCase):
    def setUp(self):
        self.estudiantes = [{'estudiante_id': 7, 'nombre': 'A', 'embedding_voz': [1., 0.]},
                            {'estudiante_id': 8, 'nombre': 'B', 'embedding_voz': [0., 1.]},
                            {'estudiante_id': 9, 'nombre': 'C', 'embedding_voz': None}]

    def construir(self, analisis):
        return construir_resultados_voz(self.estudiantes, 10, analisis, '2026-11-11T10:00:00-05:00')

    def test_distingue_presente_ausente_y_sin_muestra(self):
        filas, registros = self.construir(voz.ResultadoAudio('COMPLETADO', {7: 0.9}))
        self.assertEqual([r['estado_deteccion'] for r in registros], ['PRESENTE', 'AUSENTE', 'SIN_MUESTRA'])
        self.assertEqual([r['presente'] for r in registros], [True, False, None])
        self.assertEqual(filas[2]['Estado'], 'Sin muestra')

    def test_fallo_global_no_equivale_a_todos_ausentes_ni_admite_revision(self):
        _, registros = self.construir(voz.ResultadoAudio.fallido('ERROR_PROCESAMIENTO'))
        self.assertTrue(all(r['estado_deteccion'] == 'ANALISIS_FALLIDO' and r['presente'] is None for r in registros))
        with self.assertRaises(ValueError):
            preparar_revision(registros, [{'ID': e['estudiante_id'], 'Presente': False, 'Motivo': 'forzado'} for e in self.estudiantes])

    def test_sin_muestra_exige_decision_explicita_y_motivo_incluso_para_ausente(self):
        _, registros = self.construir(voz.ResultadoAudio('COMPLETADO', {}))
        revision = [{'ID': 7, 'Decisión': 'Ausente'}, {'ID': 8, 'Decisión': 'Ausente'},
                    {'ID': 9, 'Decisión': 'Pendiente', 'Motivo': ''}]
        with self.assertRaises(ValueError): preparar_revision(registros, revision)
        revision[2]['Decisión'] = 'Ausente'
        with self.assertRaises(ValueError): preparar_revision(registros, revision)
        revision[2]['Motivo'] = 'Lista verificada manualmente'
        r = preparar_revision(registros, revision)[2]
        self.assertIsNone(r['presente_detectado'])
        self.assertFalse(r['presente'])
        self.assertEqual(r['estado_deteccion'], 'SIN_MUESTRA')
