import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


class SelectorClaseTest(unittest.TestCase):
    def test_numero_global_no_se_presenta_como_conteo_y_no_se_hereda_seleccion(self):
        filas = [{'clase_id': 4, 'materia_id': 10, 'fecha_hora': '2026-11-22T18:00:00-05:00',
                  'estado': 'BORRADOR', 'lote_legado': 0}]
        app = AppTest.from_string('''
import streamlit as st
from src.componentes.selector_clase import selector_clase
selector_clase(st.session_state.get('materia', 10), st.session_state.get('docente', 1))
''')
        with patch('src.componentes.selector_clase.obtener_clases_profesor', return_value=filas):
            app.run()
            self.assertFalse(app.exception)
            self.assertIn('Pendiente', app.selectbox[0].options[1])
            self.assertNotIn('#4', app.selectbox[0].options[1])
            app.selectbox[0].select(4).run()
            self.assertEqual(app.selectbox[0].value, 4)
            app.session_state['docente'] = 2
            app.run()
            self.assertIsNone(app.selectbox[0].value)
            app.session_state['materia'] = 20
            app.run()
            self.assertIsNone(app.selectbox[0].value)

    def test_seleccion_fuera_de_las_clases_autorizadas_se_descarta(self):
        app = AppTest.from_string('''
from src.componentes.selector_clase import selector_clase
selector_clase(10, 2)
''')
        app.session_state['clase_selector_2_10'] = 4
        app.session_state['clase_por_seleccionar'] = {'materia_id': 10, 'profesor_id': 1, 'clase_id': 4}
        with patch('src.componentes.selector_clase.obtener_clases_profesor', return_value=[]):
            app.run()
        self.assertFalse(app.exception)
        self.assertIsNone(app.selectbox[0].value)
