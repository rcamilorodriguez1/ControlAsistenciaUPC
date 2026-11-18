import unittest
from unittest.mock import patch

from src.servicios.seguridad_claves import evaluar_clave
from src.componentes.seguridad_claves import mostrar_fortaleza, mostrar_coincidencia


class SeguridadClavesTest(unittest.TestCase):
    def test_comunes_secuencias_y_repeticiones_no_se_presentan_como_fuertes(self):
        for valor in ('12345678', 'P@ssw0rd!', 'aaaaaaaaaaaaaaaa', 'qwertyuiop'):
            with self.subTest(tipo='patron_comun'):
                self.assertLess(evaluar_clave(valor).puntuacion, 3)

    def test_frase_larga_y_datos_personales_influyen_en_la_estimacion(self):
        self.assertGreaterEqual(evaluar_clave('Faro!Nube7Bosque*Reloj26').puntuacion, 3)
        resultado = evaluar_clave('MarielaQuintero2026', nombre='Mariela Quintero', usuario='mariela.quintero')
        self.assertLess(resultado.puntuacion, 3)
        self.assertTrue(any('nombre' in consejo for consejo in resultado.consejos))

    def test_vacia_limites_y_espacios_no_se_recortan(self):
        self.assertIsNone(evaluar_clave('').puntuacion)
        self.assertFalse(evaluar_clave('abc').formato_valido)
        self.assertFalse(evaluar_clave('x' * 73).formato_valido)
        self.assertFalse(evaluar_clave('á' * 37).formato_valido)
        self.assertTrue(evaluar_clave('á' * 36).formato_valido)
        self.assertFalse(evaluar_clave('contraseña\x00').formato_valido)

    def test_no_devuelve_clave_ni_retiene_terminos_personales(self):
        from zxcvbn import matching
        anterior = matching.RANKED_DICTIONARIES.copy()
        valor = 'Faro!Nube7Bosque*Reloj26'
        resultado = evaluar_clave(valor, usuario='identificadorprivado', nombre='Persona De Prueba')
        self.assertNotIn(valor, repr(resultado))
        self.assertEqual(matching.RANKED_DICTIONARIES, anterior)
        with patch('zxcvbn.zxcvbn', side_effect=RuntimeError('fallo simulado')):
            with self.assertRaises(RuntimeError): evaluar_clave(valor, nombre='Otro nombre privado')
        self.assertEqual(matching.RANKED_DICTIONARIES, anterior)

    def test_html_solo_muestra_evaluacion_y_coincidencia_sin_la_clave(self):
        valor = 'Faro!Nube7Bosque*Reloj26'
        with patch('streamlit.html') as mostrar:
            mostrar_fortaleza(valor)
            mostrar_coincidencia(valor, '')
            mostrar_coincidencia(valor, valor + ' ')
            mostrar_coincidencia(valor, valor)
        html = [c.args[0] for c in mostrar.call_args_list]
        self.assertTrue(all(valor not in bloque for bloque in html))
        self.assertIn('Fortaleza:', html[0])
        self.assertIn('Repite', html[1])
        self.assertIn('no coinciden', html[2])
        self.assertIn('contraseñas coinciden', html[3])
