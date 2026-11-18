import unittest
from streamlit.testing.v1 import AppTest


class SeguridadClavesInterfazTest(unittest.TestCase):
    def test_fortaleza_y_confirmacion_se_actualizan_y_no_renderizan_la_clave(self):
        at = AppTest.from_file('../principal.py', default_timeout=30).run()
        next(b for b in at.button if b.label == 'Portal del Profesor').click().run()
        next(b for b in at.button if b.label == 'Registrarme en su lugar').click().run()
        self.assertFalse(at.exception)
        def html(): return ''.join(e.proto.body for e in at.get('html'))
        at.text_input[2].input('12345678').run()
        self.assertIn('Fortaleza: Muy débil', html())
        at.text_input[3].input('OtraClaveDePrueba!').run()
        self.assertIn('Las contraseñas no coinciden.', html())
        fuerte = 'Faro!Nube7Bosque*Reloj26'
        at.text_input[2].input(fuerte).run()
        self.assertIn('Fortaleza: Muy fuerte', html())
        at.text_input[3].input(fuerte).run()
        self.assertIn('Las contraseñas coinciden.', html())
        self.assertNotIn(fuerte, html())
        self.assertFalse(at.exception)
        next(b for b in at.button if b.label == 'Iniciar Sesión en su lugar').click().run()
        self.assertTrue(all(i.value == '' for i in at.text_input))
