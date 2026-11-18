import unittest
from unittest.mock import patch
import numpy as np

from src.servicios.identificacion import ClasificadorReferencias
from src.servicios.evaluacion_reconocimiento import evaluar, calibrar


def facial(valor): return np.full(128, valor)


class ReconocimientoTest(unittest.TestCase):
    def test_cero_una_y_varias_identidades_no_necesitan_entrenamiento(self):
        self.assertEqual(ClasificadorReferencias({}).identificar(facial(.1)).motivo, 'SIN_REFERENCIAS')
        for referencias in [{1: facial(.1)}, {1: facial(.1), 2: facial(.2), 3: facial(.3)}]:
            modelo = ClasificadorReferencias(referencias)
            self.assertEqual(modelo.identificar(facial(.101)).identidad, 1)
            self.assertEqual(modelo.identificar(facial(.9)).motivo, 'DESCONOCIDO')

    def test_ambiguedad_y_perfil_ajeno_no_se_reasignan_a_la_matricula(self):
        modelo = ClasificadorReferencias({1: facial(.1), 2: facial(.12)})
        self.assertEqual(modelo.identificar(facial(.11)).motivo, 'AMBIGUO')
        self.assertEqual(modelo.identificar(facial(.12), permitidos={1}).motivo, 'FUERA_DE_MATRICULA')
        self.assertIsNone(modelo.identificar(facial(.12), permitidos=set()).identidad)

    def test_voz_compara_coseno_y_rechaza_empates_y_desconocidos(self):
        a, b = np.eye(256)[:2]
        self.assertEqual(ClasificadorReferencias({1: a}, 'voz').identificar(a).identidad, 1)
        self.assertEqual(ClasificadorReferencias({1: a}, 'voz').identificar(b).motivo, 'DESCONOCIDO')
        self.assertEqual(ClasificadorReferencias({1: a, 2: a}, 'voz').identificar(a).motivo, 'AMBIGUO')

    def test_referencia_corrupta_y_ajustes_invalidos_no_se_ocultan(self):
        for vector in [[1], [float('nan')] * 128, [0] * 128]:
            with self.assertRaises(ValueError): ClasificadorReferencias({1: vector})
        modelo = ClasificadorReferencias({1: facial(.1)})
        for ajuste in [{'umbral': float('nan')}, {'margen': 0}, {'umbral': -1}]:
            with self.assertRaises(ValueError): modelo.identificar(facial(.1), **ajuste)

    def test_canalizacion_preserva_roster_y_no_inventa_confianza(self):
        from src.canalizaciones import canalizacion_facial as modulo
        modelo = ClasificadorReferencias({1: facial(.1), 2: facial(.2)})
        with patch.object(modulo, 'obtener_modelo_entrenado', return_value=modelo), patch.object(modulo, 'obtener_embeddings_faciales', return_value=[facial(.2)]):
            self.assertEqual(modulo.predecir_asistencia(None, permitidos={1}), ({}, [1], 1))

    def test_evaluacion_distingue_error_y_desconocido_y_no_aplica_calibracion(self):
        datos = {'origen': 'sintetico', 'modalidad': 'facial', 'referencias': [{'id': 1, 'vector': facial(.1).tolist()}],
                 'consultas': [{'esperado': 1, 'vector': facial(.101).tolist()}] * 10 +
                              [{'esperado': None, 'vector': facial(.9).tolist()}] * 10}
        resultado = evaluar(datos)
        self.assertEqual((resultado['far'], resultado['frr']), (0, 0))
        self.assertIsNotNone(calibrar(datos)['propuesta'])
        datos['origen'] = 'consentido'
        with self.assertRaises(ValueError): evaluar(datos)
        datos['consentimiento'] = True
        self.assertEqual(evaluar(datos)['consultas'], 20)


if __name__ == '__main__': unittest.main()
