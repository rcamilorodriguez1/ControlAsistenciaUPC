import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from streamlit.util import calc_hash

from soporte_perfil import filas_perfil
from soporte_sesiones import simular_sesiones
from src.servicios.sesiones_servidor import SesionInvalida
from src.utilidades.sesiones import iniciar_sesion


class PerfilInterfazTest(unittest.TestCase):
    def setUp(self):
        simular_sesiones(self)
        p = patch('src.servicios.perfil_estudiante.consultar_datos', return_value=filas_perfil(7))
        self.consultar = p.start(); self.addCleanup(p.stop)
        for nombre, valor in (
            ('obtener_resumen_estudiante', {'total_materias': 0, 'total_clases': 0, 'asistencia_promedio': 0}),
            ('obtener_materias_estudiante', []), ('obtener_asistencia_estudiante', []),
        ):
            p = patch('src.pantallas.pantalla_estudiante.'+nombre, return_value=valor)
            p.start(); self.addCleanup(p.stop)

    def crear(self, rol='estudiante', ruta='mi-perfil', mes=date(2026, 11, 1)):
        estado = {}
        if rol:
            iniciar_sesion(rol, {rol+'_id': 7, 'nombre': 'Estudiante de prueba', 'usuario': 'fixture'}, estado)
        at = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'principal.py'), default_timeout=35)
        for k, v in estado.items(): at.session_state[k] = v
        at.session_state['perfil_mes'] = mes
        at._page_hash = calc_hash(ruta)
        at.run(); self.assertFalse(at.exception)
        return at

    def test_perfil_muestra_metricas_y_menu_de_materias(self):
        at = self.crear()
        self.consultar.assert_called_with(7)
        self.assertEqual(len(at.expander), 5)
        self.assertEqual(at.session_state['rol_usuario'], 'estudiante')
        html = ''.join(e.proto.body for e in at.main.get('html'))
        self.assertIn('80,8', html)
        self.assertIn('data-estado="mixto"', html)
        self.assertIn('data-estado="ausente"', html)
        self.assertIn('data-estado="sin-registros"', html)
        self.assertIn('Materias matriculadas</span><strong>4</strong>', html)

    def test_mi_perfil_desde_portada_conserva_sesion(self):
        at = self.crear(ruta='')
        token = at.session_state['sesion_token']
        self.assertFalse(at.button(key='mi_perfil_cuenta').disabled)
        at.button(key='mi_perfil_cuenta').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['_vista_estudiante'], 'perfil')
        self.assertEqual(at.session_state['sesion_token'], token)

    def test_navegacion_mensual_cambio_de_anio_y_regreso_a_portal(self):
        at = self.crear(mes=date(2026, 12, 1))
        token = at.session_state['sesion_token']
        at.button(key='perfil_mes_siguiente').click().run()
        self.assertEqual(at.session_state['perfil_mes'], date(2027, 1, 1))
        at.button(key='perfil_mes_anterior').click().run()
        self.assertEqual(at.session_state['perfil_mes'], date(2026, 12, 1))
        at.button(key='perfil_volver_portal').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['_vista_estudiante'], 'portal')
        self.assertEqual(at.session_state['sesion_token'], token)

    def test_ruta_protegida_y_url_no_suplantan_rol(self):
        for rol in (None, 'profesor', 'administrador'):
            self.consultar.reset_mock()
            at = self.crear(rol=rol)
            self.consultar.assert_not_called()
            self.assertTrue(at.camera_input)
            if rol:
                self.assertTrue(at.camera_input[0].disabled)
                self.assertTrue(any(h.value=='Ya tienes una sesión activa' for h in at.subheader))
                self.assertEqual(at.session_state['rol_usuario'], rol)

    def test_id_manipulado_en_url_se_ignora(self):
        at = self.crear()
        at.query_params['estudiante_id'] = '999999'
        at.run()
        self.assertFalse(at.exception)
        self.consultar.assert_called_with(7)

    def test_revocacion_impide_consultar_el_perfil(self):
        at = self.crear()
        self.consultar.reset_mock()
        with patch('src.servicios.sesiones_servidor.validar', side_effect=SesionInvalida('Sesión revocada.')):
            at.run()
        self.assertFalse(at.exception)
        self.assertFalse(at.session_state['sesion_iniciada'])
        self.consultar.assert_not_called()

    def test_cierre_desde_perfil_revoca_el_token(self):
        at = self.crear()
        token = at.session_state['sesion_token']
        with patch('src.servicios.sesiones_servidor.cerrar') as cerrar:
            at.button(key='loginbackbtn').click().run()
            cerrar.assert_called_once_with('estudiante', 7, token)
        self.assertFalse(at.exception)
        self.assertFalse(at.session_state['sesion_iniciada'])

    def test_nombre_y_materia_se_escapan_en_html(self):
        filas = filas_perfil(7)
        for f in filas:
            f['nombre_estudiante'] = '<img src=x onerror=alert(1)>'
            f['nombre_materia'] = '<script>alert(1)</script>'
        self.consultar.return_value = filas
        at = self.crear()
        html = ''.join(e.proto.body for e in at.main.get('html') if 'perfil-' in e.proto.body)
        self.assertNotIn('<img src=x', html)
        self.assertIn('&lt;img', html)
        self.assertNotIn('<script>alert(1)', html)

    def test_perfil_nuevo_sin_clases_no_muestra_cero_ni_estado_de_riesgo(self):
        self.consultar.return_value = [{'estudiante_id': 7, 'nombre_estudiante': 'Estudiante de prueba',
                                       'codigo_institucional': None, 'materia_id': None, 'clase_id': None}]
        at = self.crear()
        html = ''.join(e.proto.body for e in at.main.get('html') if 'perfil-' in e.proto.body)
        self.assertFalse(at.expander)
        self.assertIn('perfil-estado--sin-registros', html)
        self.assertNotIn('perfil-estado--riesgo', html)
        self.assertIn('sin registros', html)
