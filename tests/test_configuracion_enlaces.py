import os
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from src.configuracion import obtener_configuracion
from src.utilidades.enlaces import crear_enlace_union


class ConfiguracionYEnlacesTest(unittest.TestCase):
    def test_el_entorno_tiene_prioridad_sobre_los_secretos(self):
        with patch.dict(os.environ, {'APP_BASE_URL': 'https://equipo.local:8501'}):
            with patch('src.configuracion.st.secrets', {'APP_BASE_URL': 'https://otro.local'}):
                self.assertEqual(obtener_configuracion('APP_BASE_URL'), 'https://equipo.local:8501')

    def test_qr_local_y_codigo_con_caracteres_especiales(self):
        with patch.dict(os.environ, {}, clear=True), patch('src.configuracion.st.secrets', {}):
            url = crear_enlace_union('BD / sección & 1')
        partes = urlsplit(url)
        self.assertEqual((partes.scheme, partes.netloc), ('https', 'localhost:8501'))
        self.assertEqual(parse_qs(partes.query)['join-code'], ['BD / sección & 1'])

    def test_rechaza_urls_que_no_pueden_ser_un_origen_de_qr(self):
        for url in ['https;//localhost:8501', 'https://usuario:clave@localhost',
                    'https://localhost:99999', 'https://localhost:0',
                    'https://local host:8501', 'https://localhost/?x=1',
                    'https://localhost/#fragmento', 'javascript:alert(1)', 'https://:8501']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                crear_enlace_union('BD101', url)

    def test_oracle_sin_clave_falla_antes_de_intentar_conectar(self):
        import src.base_datos.configuracion as config
        with patch.object(config, 'ORACLE_CONTRASENA', None), patch.object(config.oracledb, 'create_pool') as crear:
            with self.assertRaisesRegex(ValueError, 'Falta configurar Oracle'):
                config.obtener_pool()
            crear.assert_not_called()


if __name__ == '__main__':
    unittest.main()
