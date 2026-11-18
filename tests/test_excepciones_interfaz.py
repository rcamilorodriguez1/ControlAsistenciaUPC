from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from streamlit.util import calc_hash

from soporte_sesiones import simular_sesiones
from src.servicios.verificacion_identidad import PruebaIdentidad
from src.utilidades.sesiones import iniciar_sesion


class ExcepcionesInterfazTest(unittest.TestCase):
    def setUp(self):
        simular_sesiones(self)
        for nombre, valor in (
            ('obtener_resumen_estudiante', {'total_materias': 0, 'total_clases': 0, 'asistencia_promedio': 0}),
            ('obtener_materias_estudiante', []), ('obtener_asistencia_estudiante', []),
        ):
            p = patch('src.pantallas.pantalla_estudiante.' + nombre, return_value=valor)
            p.start(); self.addCleanup(p.stop)
        self.at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'principal.py'), default_timeout=35)

    def crear(self, rol=None, ruta='estudiante'):
        if rol:
            estado = {}
            iniciar_sesion(rol, {rol + '_id': 7, 'nombre': 'Fixture', 'usuario': 'fixture'}, estado)
            for k, v in estado.items():
                self.at.session_state[k] = v
        self.at._page_hash = calc_hash(ruta)
        self.at.run()
        self.assertFalse(self.at.exception)
        return self.at

    def boton(self, etiqueta):
        return next(b for b in self.at.button if b.label == etiqueta)

    def texto(self, etiqueta):
        return next(i for i in self.at.text_input if i.label == etiqueta)

    def test_alternativa_no_necesita_camara_y_muestra_estado_excepcional(self):
        at = self.crear()
        self.assertTrue(any('validación biométrica' in e.label for e in at.expander))
        self.texto('Número de documento').input('123456789')
        self.texto('Contraseña de acceso alternativo').input('ClaveSinteticaSolamente!')
        token_anterior = at.session_state['sesion_token']
        perfil = {'estudiante_id': 7, 'nombre': 'Fixture', '_prueba_identidad': PruebaIdentidad(7, 'EXCEPCION', 0, 0, 'fixture')}
        with patch('src.componentes.acceso_excepcional.autenticar_excepcion', return_value=perfil) as autenticar:
            self.boton('Ingresar mediante excepción').click().run()
        self.assertFalse(at.exception)
        autenticar.assert_called_once_with('CC', '123456789', 'ClaveSinteticaSolamente!')
        self.assertEqual(at.session_state['datos_estudiante']['estado_verificacion'], 'EXCEPCIONAL')
        self.assertNotIn('_prueba_identidad', at.session_state['datos_estudiante'])
        for campo in ('documento', 'clave', 'tipo'):
            self.assertNotIn(f'auth_estudiante_{campo}_{token_anterior}', at.session_state)
        self.assertTrue(any('Verificación excepcional' in w.value for w in at.warning))

    def test_fallo_alternativo_conserva_formulario_y_no_abre_sesion(self):
        self.crear()
        with patch('src.componentes.acceso_excepcional.autenticar_excepcion', return_value=None):
            self.boton('Ingresar mediante excepción').click().run()
        self.assertFalse(self.at.exception)
        self.assertFalse(self.at.session_state['sesion_iniciada'])
        self.assertTrue(any('No se pudo validar' in e.value for e in self.at.error))
        self.assertEqual(len(self.at.camera_input), 1)

    def test_conflicto_desactiva_tambien_el_acceso_alternativo(self):
        self.crear('profesor')
        self.assertTrue(self.boton('Ingresar mediante excepción').disabled)
        self.assertTrue(self.texto('Número de documento').disabled)
        self.assertTrue(self.texto('Contraseña de acceso alternativo').disabled)
        self.assertEqual(self.at.session_state['rol_usuario'], 'profesor')

    def test_administracion_ofrece_alta_sin_biometria_y_revocacion(self):
        fila = dict(estudiante_id=7, nombre='Fixture', codigo_institucional='TEST-7', activo=1,
            estado_verificacion='EXCEPCIONAL', excepcion_activa=1, excepcion_vigente=1, version_credencial=3)
        with patch('src.servicios.excepciones_biometricas.listar', return_value=[fila]):
            self.crear('administrador', 'administracion')
            self.at.radio(key='admin_modulo').set_value('Verificación').run()
            self.assertFalse(self.at.exception)
            self.assertTrue(self.boton('Autorizar excepción'))
            cuenta = next(s for s in self.at.selectbox if s.label == 'Cuenta para gestionar')
            cuenta.set_value(7).run()
            self.assertFalse(self.at.exception)
            self.texto('Motivo administrativo de revocación').input('Fin del expediente sintético')
            with patch('src.servicios.excepciones_biometricas.revocar') as revocar:
                self.boton('Revocar excepción y cerrar sesión').click().run()
            revocar.assert_called_once_with(7, 'Fin del expediente sintético', version=3)
            self.assertFalse(self.at.exception)

    def test_administracion_no_autoriza_con_confirmacion_distinta(self):
        with patch('src.servicios.excepciones_biometricas.listar', return_value=[]):
            self.crear('administrador', 'administracion')
            self.at.radio(key='admin_modulo').set_value('Verificación').run()
            self.texto('Contraseña alternativa (mínimo 12 caracteres)').input('ClaveSinteticaUnica!')
            self.texto('Confirmar contraseña alternativa').input('OtraClaveSintetica!')
            with patch('src.servicios.excepciones_biometricas.autorizar') as autorizar:
                self.boton('Autorizar excepción').click().run()
            autorizar.assert_not_called()
            self.assertFalse(self.at.exception)
            self.assertTrue(any('no coinciden' in w.value for w in self.at.warning))
