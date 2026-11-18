import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from src.canalizaciones import canalizacion_facial as facial
from src.utilidades.biometria import MuestraInvalida


class CapturaFacialTest(unittest.TestCase):
    def setUp(self):
        self.imagen = np.zeros((256, 256, 3), dtype=np.uint8)
        self.detector, self.predictor, self.codificador = MagicMock(), MagicMock(), MagicMock()
        self.rectangulo = MagicMock()
        for nombre, valor in [('width', 100), ('height', 100), ('left', 20), ('top', 20), ('right', 120), ('bottom', 120)]:
            getattr(self.rectangulo, nombre).return_value = valor
        self.detector.return_value = [self.rectangulo]
        self.codificador.compute_face_descriptor.return_value = np.full(128, 0.1)
        parche = patch.object(facial, 'cargar_modelos_dlib', return_value=(self.detector, self.predictor, self.codificador))
        parche.start()
        self.addCleanup(parche.stop)

    def test_registro_rechaza_cero_y_varios_rostros_sin_codificar(self):
        for rostros in [[], [self.rectangulo, self.rectangulo]]:
            self.detector.return_value = rostros
            with self.assertRaises(MuestraInvalida):
                facial.obtener_embeddings_faciales(self.imagen, rostro_unico=True)
        self.codificador.compute_face_descriptor.assert_not_called()

    def test_registro_rechaza_rostro_pequeno_o_recortado(self):
        self.rectangulo.width.return_value = 40
        with self.assertRaises(MuestraInvalida): facial.obtener_embeddings_faciales(self.imagen, rostro_unico=True)
        self.rectangulo.width.return_value = 100
        self.rectangulo.left.return_value = -1
        with self.assertRaises(MuestraInvalida): facial.obtener_embeddings_faciales(self.imagen, rostro_unico=True)
        self.codificador.compute_face_descriptor.assert_not_called()

    def test_descriptor_valido_conserva_escala_y_tipo_rgb(self):
        salida = facial.obtener_embeddings_faciales(self.imagen, rostro_unico=True)
        np.testing.assert_array_equal(salida[0], np.full(128, 0.1))
        self.assertEqual(self.detector.call_args.args[0].dtype, np.uint8)
        self.assertTrue(self.detector.call_args.args[0].flags.c_contiguous)

    def test_descriptor_corrupto_se_rechaza(self):
        self.codificador.compute_face_descriptor.return_value = [float('nan')] * 128
        with self.assertRaises(MuestraInvalida): facial.obtener_embeddings_faciales(self.imagen, rostro_unico=True)

    def test_toma_grupal_sigue_permitiendo_varios_rostros(self):
        self.detector.return_value = [self.rectangulo, self.rectangulo]
        self.assertEqual(len(facial.obtener_embeddings_faciales(self.imagen)), 2)

    def test_invalidacion_solo_afecta_al_clasificador_facial(self):
        with patch.object(facial.obtener_modelo_entrenado, 'clear') as limpiar, patch('streamlit.cache_resource.clear') as global_:
            facial.invalidar_modelo_facial()
            limpiar.assert_called_once()
            global_.assert_not_called()
