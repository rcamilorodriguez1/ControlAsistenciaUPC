import unittest
from unittest.mock import patch, MagicMock

import numpy as np

from src.canalizaciones import canalizacion_voz as voz
from src.utilidades.biometria import MuestraInvalida
from test_muestras_biometricas import audio_wav


class RegistroVozTest(unittest.TestCase):
    def test_silencio_o_sin_actividad_vocal_no_carga_codificador(self):
        with patch.object(voz, 'cargar_codificador_voz') as cargar:
            with self.assertRaises(MuestraInvalida): voz.obtener_embedding_voz(audio_wav(amplitud=0))
            with patch('src.utilidades.muestra_voz.webrtcvad.Vad') as vad:
                vad.return_value.is_speech.return_value = False
                with self.assertRaises(MuestraInvalida): voz.obtener_embedding_voz(audio_wav())
            cargar.assert_not_called()

    def test_voz_valida_y_vector_se_normalizan_antes_de_devolverlos(self):
        encoder = MagicMock()
        encoder.embed_utterance.return_value = np.full(256, 2.)
        with patch('src.utilidades.muestra_voz.webrtcvad.Vad') as vad, patch.object(
                voz, 'preprocess_wav', side_effect=lambda a: a), patch.object(
                voz, 'cargar_codificador_voz', return_value=encoder):
            vad.return_value.is_speech.return_value = True
            vector = voz.obtener_embedding_voz(audio_wav())
        self.assertEqual(len(vector), 256)
        self.assertAlmostEqual(np.linalg.norm(vector), 1.)
        encoder.embed_utterance.assert_called_once()

    def test_preprocesamiento_sin_voz_o_vector_invalido_no_se_guarda(self):
        for salida, vector in [(np.array([]), np.ones(256)), (np.full(48000, np.nan), np.ones(256)),
                               (np.ones(48000), np.ones(128)), (np.ones(48000), np.zeros(256))]:
            with self.subTest(dimension=len(vector)), patch('src.utilidades.muestra_voz.webrtcvad.Vad') as vad, patch.object(
                    voz, 'preprocess_wav', return_value=salida), patch.object(voz, 'cargar_codificador_voz') as cargar:
                vad.return_value.is_speech.return_value = True
                cargar.return_value.embed_utterance.return_value = vector
                with self.assertRaises(MuestraInvalida): voz.obtener_embedding_voz(audio_wav())
                if len(salida) == 0 or not np.isfinite(salida).all(): cargar.assert_not_called()

    def test_comparacion_coseno_no_depende_de_escala_del_vector_guardado(self):
        eje0, eje1 = np.eye(256)[:2]
        referencia = eje0 * 40
        sid, puntaje = voz.identificar_hablante(eje0 * 3, {7: referencia, 8: eje1 * 100})
        self.assertEqual(sid, 7)
        self.assertAlmostEqual(puntaje, 1.)
        np.testing.assert_array_equal(referencia, eje0 * 40)
