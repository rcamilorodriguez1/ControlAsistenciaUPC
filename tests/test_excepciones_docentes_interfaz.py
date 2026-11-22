import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


class ExcepcionesDocentesInterfazTest(unittest.TestCase):
    def setUp(self):
        alumno = dict(estudiante_id=7, nombre='Alumno de prueba', codigo_institucional='TEST-7',
            excepcion_activa=0, excepcion_vigente=0, expira_en=None, version_credencial=0,
            puede_autorizar=1, puede_revocar=0)
        self.alumno = alumno
        for nombre, valor in (
            ('src.componentes.excepciones_docentes.obtener_actor', ('profesor', 1, 'token-fixture')),
            ('src.componentes.excepciones_docentes.obtener_materias_profesor', [dict(materia_id=10, nombre='Materia de prueba', codigo_materia='BD-1')]),
            ('src.servicios.excepciones_docentes.listar', [alumno]),
        ):
            p = patch(nombre, return_value=valor); p.start(); self.addCleanup(p.stop)
        self.app = AppTest.from_string('''
from src.componentes.excepciones_docentes import gestionar_excepciones_docentes
gestionar_excepciones_docentes()
''').run()
        self.assertFalse(self.app.exception)

    def texto(self, etiqueta):
        return next(c for c in self.app.text_input if c.label == etiqueta)

    def test_no_autoriza_claves_distintas(self):
        self.texto('Clave para entregar al estudiante').input('UnaClaveSinteticaSegura!')
        self.texto('Confirmar clave').input('OtraClaveSinteticaSegura!')
        with patch('src.servicios.excepciones_docentes.autorizar') as autorizar:
            next(b for b in self.app.button if b.label == 'Autorizar y entregar clave').click().run()
        autorizar.assert_not_called()
        self.assertFalse(self.app.exception)
        self.assertTrue(any('no coinciden' in a.value for a in self.app.warning))

    def test_autorizacion_entrega_manual_y_limpia_campos_sensibles(self):
        self.texto('Número de documento').input('123456789')
        self.texto('Referencia de autorización').input('SOL-TEST')
        self.texto('Clave para entregar al estudiante').input('UnaClaveSinteticaSegura!')
        self.texto('Confirmar clave').input('UnaClaveSinteticaSegura!')
        self.app.checkbox[0].check()
        with patch('src.servicios.excepciones_docentes.autorizar') as autorizar:
            next(b for b in self.app.button if b.label == 'Autorizar y entregar clave').click().run()
        autorizar.assert_called_once_with(10, 7, 'CC', '123456789', 'UnaClaveSinteticaSegura!', 'FISICA',
            'SOL-TEST', 1, version=0, documento_comprobado=True)
        self.assertFalse(self.app.exception)
        self.assertTrue(any('Entrega la clave' in a.value for a in self.app.success))
        self.assertEqual(self.texto('Clave para entregar al estudiante').value, '')
        self.assertEqual(self.texto('Número de documento').value, '')

    def test_autorizacion_ajena_no_ofrece_formulario(self):
        self.alumno['puede_autorizar'] = 0
        self.app.run()
        self.assertFalse(self.app.exception)
        self.assertFalse(any(b.label == 'Autorizar y entregar clave' for b in self.app.button))
        self.assertTrue(any('otro docente' in a.value for a in self.app.warning))
