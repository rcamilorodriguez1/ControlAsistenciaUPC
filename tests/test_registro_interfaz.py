from io import BytesIO
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image
from streamlit.testing.v1 import AppTest

from test_muestras_biometricas import audio_wav


class RegistroInterfazTest(unittest.TestCase):
    def setUp(self):
        from soporte_sesiones import simular_sesiones
        simular_sesiones(self)
        self.parches = [
            patch('src.pantallas.pantalla_estudiante.predecir_asistencia', return_value=({}, [], 1)),
            patch('src.servicios.registro_estudiante.obtener_embeddings_faciales', return_value=[np.full(128, 0.1)]),
            patch('src.servicios.registro_estudiante.crear_estudiante', return_value=[{'estudiante_id': 7, 'nombre': 'Alumno'}]),
            patch('src.servicios.registro_estudiante.invalidar_modelo_facial'),
            patch('src.pantallas.pantalla_estudiante.obtener_resumen_estudiante', return_value={
                'total_materias': 0, 'total_clases': 0, 'asistencia_promedio': 0}),
            patch('src.pantallas.pantalla_estudiante.obtener_materias_estudiante', return_value=[]),
            patch('src.pantallas.pantalla_estudiante.obtener_asistencia_estudiante', return_value=[]),
        ]
        self.mock = [p.start() for p in self.parches]
        for p in self.parches: self.addCleanup(p.stop)
        self.at = AppTest.from_file('../principal.py', default_timeout=45)
        self.at.run()
        next(b for b in self.at.button if b.label == 'Portal del Estudiante').click().run()

    def foto(self):
        archivo = BytesIO()
        Image.new('RGB', (256, 256)).save(archivo, format='JPEG')
        self.at.camera_input[0].upload('rostro.jpg', archivo.getvalue()).run()
        self.assertEqual([e.message for e in self.at.exception], [])
        next(i for i in self.at.text_input if i.label == 'Ingresa tu nombre').input('Alumno').run()
        next(i for i in self.at.text_input if i.label == 'Código institucional').input('TEST-001').run()

    def crear(self):
        next(b for b in self.at.button if b.label == 'Crear Cuenta').click().run()
        self.assertEqual([e.message for e in self.at.exception], [])

    def test_silencio_no_se_omite_y_borrarlo_permite_registro_sin_voz(self):
        self.foto()
        self.at.audio_input[0].upload('silencio.wav', audio_wav(amplitud=0)).run()
        self.crear()
        self.mock[2].assert_not_called()
        self.assertFalse(self.at.session_state['sesion_iniciada'])
        self.assertTrue(any('silencio' in w.value for w in self.at.warning))
        self.at.audio_input[0].clear().run()
        self.crear()
        self.mock[2].assert_called_once()
        self.assertIsNone(self.mock[2].call_args.kwargs['embedding_voz'])
        self.assertTrue(self.at.session_state['sesion_iniciada'])
        self.assertNotIn('embedding_facial', self.at.session_state['datos_estudiante'])

    def test_dos_rostros_detectados_al_guardar_no_crean_perfil(self):
        self.foto()
        self.mock[1].return_value = [np.ones(128), np.ones(128)]
        self.crear()
        self.mock[2].assert_not_called()
        self.assertTrue(any('exactamente un rostro' in w.value for w in self.at.warning))

    def test_imagen_corrupta_no_llega_al_reconocimiento_ni_al_registro(self):
        self.at.camera_input[0].upload('rostro.jpg', b'contenido corrupto').run()
        self.assertEqual([e.message for e in self.at.exception], [])
        self.mock[0].assert_not_called()
        self.mock[2].assert_not_called()
        self.assertTrue(any('fotografía' in w.value for w in self.at.warning))
