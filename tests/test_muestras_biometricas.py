from io import BytesIO
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image
import soundfile as sf

from src.utilidades.biometria import MuestraInvalida, validar_vector_facial, normalizar_vector_voz
from src.utilidades.muestra_facial import leer_foto_registro
from src.utilidades.muestra_voz import cargar_audio_seguro, validar_tramo_voz
from src.servicios import registro_estudiante as registro
from src.base_datos import bd


def foto_registro(modo='RGB', tamano=(256, 256)):
    archivo = BytesIO()
    Image.new(modo, tamano).save(archivo, format='PNG')
    return archivo


def audio_wav(segundos=3, frecuencia=16000, amplitud=0.1, canales=1):
    tiempo = np.arange(int(frecuencia * segundos)) / frecuencia
    onda = amplitud * np.sin(2 * np.pi * 220 * tiempo)
    if canales > 1:
        onda = np.repeat(onda[:, None], canales, axis=1)
    salida = BytesIO()
    sf.write(salida, onda, frecuencia, format='WAV', subtype='PCM_16')
    return salida.getvalue()


class VectoresTest(unittest.TestCase):
    def test_rechaza_dimensiones_tipos_valores_no_finitos_y_vector_nulo(self):
        for n, validar in [(128, validar_vector_facial), (256, normalizar_vector_voz)]:
            for vector in [None, [], [1.] * (n - 1), [[1.] * n], [0.] * n,
                           [True] + [1.] * (n - 1), ['1'] * n, [1j] * n,
                           [float('nan')] + [1.] * (n - 1), [float('inf')] * n]:
                with self.subTest(n=n, tipo=type(vector).__name__), self.assertRaises(MuestraInvalida):
                    validar(vector)

    def test_voz_unitaria_y_descriptor_facial_conserva_su_escala(self):
        voz = np.arange(1., 257.)
        facial = np.linspace(-0.2, 0.3, 128)
        np.testing.assert_array_equal(validar_vector_facial(facial), facial)
        self.assertAlmostEqual(np.linalg.norm(normalizar_vector_voz(voz)), 1.)
        np.testing.assert_allclose(normalizar_vector_voz(voz * 100), normalizar_vector_voz(voz))

    def test_crear_estudiante_invalido_no_llega_a_oracle(self):
        casos = [(None, None), ([1.] * 127, None), ([1.] * 128, []),
                 ([1.] * 128, [1.] * 255), ([1.] * 128, [float('nan')] * 256)]
        for facial, voz in casos:
            with self.subTest(dimension_voz=len(voz) if voz else None), patch.object(bd, 'ejecutar_con_reintentos') as ejecutar:
                with self.assertRaises(MuestraInvalida):
                    bd.crear_estudiante('Alumno', facial, voz)
                ejecutar.assert_not_called()

    def test_guardado_prepara_voz_normalizada_sin_reintentar_alta(self):
        with patch.object(bd, 'ejecutar_con_reintentos', return_value=42) as ejecutar:
            datos = bd.crear_estudiante('Alumno', [0.1] * 128, [2.] * 256, codigo_institucional='TEST-001')[0]
        self.assertEqual(ejecutar.call_args.kwargs, {'reintentos': 1})
        self.assertAlmostEqual(np.linalg.norm(datos['embedding_voz']), 1.)
        np.testing.assert_array_equal(datos['embedding_facial'], [0.1] * 128)


class CalidadCapturaTest(unittest.TestCase):
    def test_foto_se_convierte_a_rgb_y_rechaza_archivo_corrupto_o_diminuto(self):
        self.assertEqual(leer_foto_registro(foto_registro('L')).shape, (256, 256, 3))
        for archivo in [BytesIO(b'invalido'), foto_registro(tamano=(10, 10))]:
            with self.assertRaises(MuestraInvalida): leer_foto_registro(archivo)
        with patch('src.utilidades.muestra_facial.MAX_BYTES_REGISTRO', 10), self.assertRaises(MuestraInvalida):
            leer_foto_registro(foto_registro())

    def test_audio_corto_largo_vacio_corrupto_silencioso_y_saturado_se_rechazan(self):
        for datos in [b'', b'no es wav', audio_wav(1), audio_wav(31), audio_wav(amplitud=0),
                      audio_wav(amplitud=0.000001)]:
            with self.subTest(bytes=len(datos)), self.assertRaises(MuestraInvalida):
                cargar_audio_seguro(datos, registro=True)
        salida = BytesIO()
        sf.write(salida, np.tile([-1., 1.], 24000), 16000, format='WAV', subtype='PCM_16')
        with self.assertRaises(MuestraInvalida): cargar_audio_seguro(salida.getvalue(), registro=True)

    def test_audio_estereo_se_convierte_a_mono_y_16khz(self):
        onda = cargar_audio_seguro(audio_wav(3, frecuencia=8000, canales=2), registro=True)
        self.assertEqual(onda.shape, (48000,))
        self.assertEqual(onda.dtype, np.float32)
        self.assertTrue(np.isfinite(onda).all())

    def test_actividad_vocal_es_obligatoria_aunque_haya_senal(self):
        onda = cargar_audio_seguro(audio_wav(), registro=True)
        with patch('src.utilidades.muestra_voz.webrtcvad.Vad') as vad:
            vad.return_value.is_speech.return_value = False
            with self.assertRaises(MuestraInvalida): validar_tramo_voz(onda)
            vad.return_value.is_speech.side_effect = [True] * 20 + [False] * 80
            with self.assertRaises(MuestraInvalida): validar_tramo_voz(onda)
            vad.return_value.is_speech.side_effect = None
            vad.return_value.is_speech.return_value = True
            self.assertEqual(validar_tramo_voz(onda).shape, onda.shape)
            vad.assert_called_with(2)


class RegistroValidadoTest(unittest.TestCase):
    def setUp(self):
        self.parches = [patch.object(registro, 'obtener_embeddings_faciales', return_value=[np.full(128, 0.1)]),
                        patch.object(registro, 'obtener_embedding_voz', return_value=[2.] * 256),
                        patch.object(registro, 'crear_estudiante', return_value=[{'estudiante_id': 1, 'nombre': 'Alumno'}]),
                        patch.object(registro, 'invalidar_modelo_facial')]
        self.mock = [p.start() for p in self.parches]
        for p in self.parches: self.addCleanup(p.stop)

    def test_exactamente_un_rostro_revalidado_antes_de_crear(self):
        for rostros in [[], [np.ones(128), np.ones(128)]]:
            self.mock[0].return_value = rostros
            with self.assertRaises(MuestraInvalida): registro.registrar_estudiante('Alumno', foto_registro(), codigo_institucional='TEST-001')
            self.mock[2].assert_not_called()
        self.assertTrue(self.mock[0].call_args.kwargs['rostro_unico'])

    def test_voz_enviada_fallida_no_se_omite_ni_crea_perfil(self):
        self.mock[1].side_effect = MuestraInvalida('Voz insuficiente')
        with self.assertRaises(MuestraInvalida): registro.registrar_estudiante('Alumno', foto_registro(), b'voz', codigo_institucional='TEST-001')
        self.mock[2].assert_not_called()
        self.mock[3].assert_not_called()

    def test_sin_voz_es_opcional_y_con_voz_se_normaliza(self):
        registro.registrar_estudiante(' Alumno ', foto_registro(), codigo_institucional='TEST-001')
        self.mock[1].assert_not_called()
        self.assertIsNone(self.mock[2].call_args.kwargs['embedding_voz'])
        registro.registrar_estudiante(' Alumno ', foto_registro(), b'voz', codigo_institucional='TEST-001')
        self.assertAlmostEqual(np.linalg.norm(self.mock[2].call_args.kwargs['embedding_voz']), 1.)
        self.assertEqual(self.mock[2].call_args.args, ('Alumno',))
        self.assertEqual(self.mock[3].call_count, 2)
