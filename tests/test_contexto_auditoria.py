import unittest
import time
from unittest.mock import patch

from src.base_datos.bd import _contexto_auditoria_actual


class ContextoDeAplicacionTest(unittest.TestCase):
    def test_sin_sesion_streamlit_no_inventa_actor(self):
        with patch('streamlit.runtime.scriptrunner.get_script_run_ctx', return_value=None):
            self.assertIsNone(_contexto_auditoria_actual())

    def test_cerrar_sesion_invalida_el_actor_aunque_quede_el_perfil(self):
        estado = {'sesion_iniciada': False, 'rol_usuario': 'profesor', 'datos_profesor': {'profesor_id': 123}}
        with patch('streamlit.runtime.scriptrunner.get_script_run_ctx', return_value=object()), patch('streamlit.session_state', estado):
            self.assertIsNone(_contexto_auditoria_actual())

    def test_usa_el_rol_y_perfil_actuales(self):
        for rol, perfil, clave, actor in [('profesor', 'datos_profesor', 'profesor_id', 123),
                                          ('estudiante', 'datos_estudiante', 'estudiante_id', 456)]:
            estado = {'sesion_iniciada': True, 'rol_usuario': rol, 'tipo_sesion': rol,
                      'sesion_token': 'sesion-de-prueba', perfil: {clave: actor},
                      'sesion_creada_en': time.time(), 'sesion_actividad_en': time.time()}
            with self.subTest(rol=rol), patch('streamlit.runtime.scriptrunner.get_script_run_ctx', return_value=object()), patch('streamlit.session_state', estado):
                self.assertEqual(_contexto_auditoria_actual(), (rol.upper(), actor, None))

    def test_el_portal_elegido_no_cambia_el_actor_de_auditoria(self):
        estado = {'sesion_iniciada': True, 'rol_usuario': 'profesor', 'tipo_sesion': 'estudiante',
                  'sesion_token': 'prueba', 'datos_profesor': {'profesor_id': 123},
                  'sesion_creada_en': time.time(), 'sesion_actividad_en': time.time()}
        with patch('streamlit.runtime.scriptrunner.get_script_run_ctx', return_value=object()), patch('streamlit.session_state', estado):
            self.assertEqual(_contexto_auditoria_actual(), ('PROFESOR', 123, None))


if __name__ == '__main__':
    unittest.main()
