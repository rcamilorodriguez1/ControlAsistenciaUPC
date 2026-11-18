import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from src.utilidades.sesiones import iniciar_sesion


class GestionInterfazTest(unittest.TestCase):
    def setUp(self):
        from soporte_sesiones import simular_sesiones
        simular_sesiones(self)
        self.at = AppTest.from_string('from src.componentes.gestion_cuenta import gestion_cuenta\ngestion_cuenta()', default_timeout=30)
        estado = {}
        iniciar_sesion('estudiante', {'estudiante_id': 7, 'nombre': 'Alumno'}, estado)
        for clave, valor in estado.items(): self.at.session_state[clave] = valor

    def test_retirar_biometria_requiere_confirmacion_y_cierra_la_sesion(self):
        self.at.run()
        boton = self.at.button[0]
        self.assertTrue(boton.disabled)
        self.at.text_input[0].input('Revocar biometría').run()
        self.at.checkbox[0].check().run()
        with patch('src.base_datos.gestion.retirar_biometria') as retirar:
            self.at.button[0].click().run()
        retirar.assert_called_once_with(7, 'Revocar biometría')
        self.assertEqual(len(self.at.exception), 0)
        self.assertFalse(self.at.session_state['sesion_iniciada'])

    def test_error_de_permiso_no_cierra_la_sesion_ni_oculta_el_motivo(self):
        self.at.run()
        self.at.text_input[0].input('Revocar biometría')
        self.at.checkbox[0].check().run()
        with patch('src.base_datos.gestion.retirar_biometria', side_effect=PermissionError('Cuenta no autorizada')):
            self.at.button[0].click().run()
        self.assertTrue(self.at.session_state['sesion_iniciada'])
        self.assertEqual(self.at.warning[0].value, 'Cuenta no autorizada')
