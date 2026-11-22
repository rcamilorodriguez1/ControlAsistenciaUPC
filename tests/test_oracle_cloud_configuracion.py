import importlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
cloud = importlib.import_module('probar_oracle_cloud')


class ConexionCloudTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.archivo = Path(self.temporal.name) / 'dsn.txt'
        self.dsn = ('(description=(retry_count=20)(retry_delay=3)'
                    '(address=(protocol=tcps)(port=1522)(host=adb.us-ashburn-1.oraclecloud.com))'
                    '(connect_data=(service_name=fixture_low.adb.oraclecloud.com))'
                    '(security=(ssl_server_dn_match=yes)))')
        self.archivo.write_text(self.dsn, encoding='utf-8')

    def test_descriptor_tls_conserva_servicio_y_limita_reintentos(self):
        parametros = cloud.leer_parametros(self.archivo)
        self.assertEqual(parametros.protocol, 'tcps')
        self.assertEqual(parametros.service_name, 'fixture_low.adb.oraclecloud.com')
        self.assertTrue(parametros.ssl_server_dn_match)
        self.assertEqual(parametros.retry_count, 0)
        self.assertEqual(parametros.tcp_connect_timeout, 10)

    def test_rechaza_escape_tcp_y_verificacion_desactivada(self):
        for dsn in (self.dsn.replace('.adb.', r'\.adb.'),
                    self.dsn.replace('protocol=tcps', 'protocol=tcp'),
                    self.dsn.replace('ssl_server_dn_match=yes', 'ssl_server_dn_match=no'),
                    self.dsn.replace('adb.us-ashburn-1.oraclecloud.com', 'localhost')):
            with self.subTest(dsn=dsn):
                self.archivo.write_text(dsn, encoding='utf-8')
                with self.assertRaises(ValueError):
                    cloud.leer_parametros(self.archivo)

    def test_prueba_usa_sql_externo_y_no_confunde_claves_locales(self):
        parametros = cloud.leer_parametros(self.archivo)
        conexion = MagicMock()
        conexion.__enter__.return_value.version = '26.0.fixture'
        cursor = conexion.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ('ADMIN', 'FIXTURE', 'fixture_low.adb.oraclecloud.com')
        with patch.object(cloud.oracledb, 'connect', return_value=conexion) as conectar:
            resultado = cloud.probar_conexion(parametros, 'ADMIN', 'solo-fixture')
        conectar.assert_called_once_with(user='ADMIN', password='solo-fixture', params=parametros)
        consulta = cursor.execute.call_args.args[0]
        self.assertTrue(consulta.startswith('SELECT USER'))
        self.assertNotIn('solo-fixture', consulta)
        self.assertEqual(resultado['usuario'], 'ADMIN')
        conexion.__enter__.return_value.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
