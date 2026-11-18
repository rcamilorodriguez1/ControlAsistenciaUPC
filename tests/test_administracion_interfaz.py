import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from src.utilidades.sesiones import iniciar_sesion


class AdministracionInterfazTest(unittest.TestCase):
    def setUp(self):
        from soporte_sesiones import simular_sesiones
        simular_sesiones(self)
        self.perfil = {'administrador_id': 77, 'usuario': 'admin.fixture', 'nombre': 'Administración de prueba'}
        self.parches = [
            patch('src.base_datos.administracion.cuentas', return_value=[{'id': 7, 'usuario': 'docente.fixture', 'nombre': 'Docente', 'activo': 1, 'version': '0'}]),
            patch('src.base_datos.administracion.materias', return_value=[{'id': 10, 'codigo_materia': 'BD-1', 'nombre': 'Bases', 'seccion': 'A', 'profesor_id': 7, 'profesor': 'Docente', 'activo': 1, 'clases': 2, 'version': '0'}]),
            patch('src.base_datos.administracion.auditoria', return_value=[{'evento_id': 1, 'accion': 'EDICION_CUENTA', 'motivo': 'Prueba'}]),
            patch('src.base_datos.administracion.exportar_csv', return_value=b'evento_id\n1\n'),
            patch('src.base_datos.administracion.editar_profesor'),
            patch('src.base_datos.administracion.editar_estudiante'),
            patch('src.base_datos.administracion.editar_materia')]
        self.mock = [p.start() for p in self.parches]
        for p in self.parches: self.addCleanup(p.stop)
        self.at = AppTest.from_file('../principal.py', default_timeout=30)

    def entrar(self):
        from streamlit.util import calc_hash
        self.at._page_hash = calc_hash('administracion')
        estado = {}; iniciar_sesion('administrador', self.perfil, estado)
        for key, valor in estado.items(): self.at.session_state[key] = valor
        self.at.run()

    def boton(self, nombre): return next(b for b in self.at.button if b.label == nombre)
    def texto(self, nombre): return next(i for i in self.at.text_input if i.label == nombre)
    def comprobar(self): self.assertFalse(self.at.exception)

    def test_acceso_separado_sin_registro_publico_y_logout_limpia_resultados(self):
        self.at.run(); self.boton('Gestión académica').click().run(); self.comprobar()
        self.assertEqual([i.label for i in self.at.text_input], ['Usuario administrativo', 'Contraseña'])
        self.assertFalse(any('Registr' in b.label for b in self.at.button))
        self.at.text_input[0].input('admin.fixture'); self.at.text_input[1].input('ClaveDePrueba')
        with patch('src.base_datos.administracion.autenticar', return_value={**self.perfil, 'contrasena': 'NO_GUARDAR'}):
            self.boton('Ingresar a Administración').click().run()
        self.assertNotIn('contrasena', self.at.session_state['datos_administrador'])
        self.at.session_state['admin_csv'] = b'privado'
        self.at.button(key='loginbackbtn').click().run(); self.comprobar()
        self.assertFalse(self.at.session_state['sesion_iniciada'])
        self.assertNotIn('admin_csv', self.at.session_state)

    def test_auditoria_exporta_sin_ofrecer_editar_historial(self):
        self.entrar(); self.boton('Consultar auditoría').click().run(); self.comprobar()
        self.boton('Generar CSV de estos resultados').click().run(); self.comprobar()
        self.mock[3].assert_called_once()
        self.assertTrue(self.at.get('download_button'))
        for guardar in self.mock[4:]: guardar.assert_not_called()

    def test_edicion_requiere_confirmacion_y_envia_motivo_y_version(self):
        self.entrar(); self.at.radio[0].set_value('Cuentas').run(); self.comprobar()
        self.assertTrue(self.boton('Guardar cambios de cuenta').disabled)
        self.texto('Nombre completo').input('Docente actualizado')
        self.texto('Motivo del cambio').input('Corrección de nombre')
        next(c for c in self.at.checkbox if c.label == 'He revisado los cambios de esta cuenta').check().run()
        self.boton('Guardar cambios de cuenta').click().run(); self.comprobar()
        self.mock[4].assert_called_once_with(7, 'docente.fixture', 'Docente actualizado', True, 'Corrección de nombre', '', version='0')

    def test_error_de_version_conserva_panel_y_no_sobrescribe(self):
        self.entrar(); self.at.radio[0].set_value('Materias').run(); self.comprobar()
        self.assertTrue(next(s for s in self.at.selectbox if s.label == 'Profesor responsable').disabled)
        self.texto('Motivo del cambio de materia').input('Actualizar catálogo')
        next(c for c in self.at.checkbox if c.label == 'He revisado los cambios de esta materia').check().run()
        self.mock[6].side_effect = ValueError('El registro cambió; recarga los datos.')
        self.boton('Guardar cambios de materia').click().run(); self.comprobar()
        self.assertTrue(any('registro cambió' in w.value for w in self.at.warning))
