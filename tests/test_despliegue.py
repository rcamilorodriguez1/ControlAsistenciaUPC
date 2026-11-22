import base64
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.configuracion import obtener_configuracion
from src.base_datos.transporte import parametros_transporte
from src.servicios.despliegue import validar_configuracion, comando_streamlit, comprobar_base


class DespliegueTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name)
        self.clave = self.ruta / 'identidad.key'
        self.clave.write_bytes(b'x' * 32)
        self.config = {
            'APP_BASE_URL': 'https://aula.example.com', 'ORACLE_USUARIO': 'UPC_AULA_APP',
            'ORACLE_ESQUEMA': 'UPC_ASISTENCIA',
            'ORACLE_CONTRASENA': 'solo-fixture-no-utilizable',
            'ORACLE_DSN': 'tcps://db.example.com:1522/servicio_low', 'ORACLE_TLS_MODO': 'tls',
            'ORACLE_ADMIN_USUARIO': 'UPC_ADMIN_APP', 'ORACLE_ADMIN_CONTRASENA': 'otro-fixture',
            'PROFESOR_CLAVE_ALTA': 'autorizacion-fixture', 'IDENTIDAD_CLAVE_RUTA': str(self.clave),
        }
        entorno = patch.dict(os.environ, {}, clear=True)
        entorno.start(); self.addCleanup(entorno.stop)
        secretos = patch('src.configuracion.st.secrets', self.config)
        secretos.start(); self.addCleanup(secretos.stop)

    def test_archivo_privado_y_prioridad_del_entorno(self):
        archivo = self.ruta / 'password'
        archivo.write_text('secreto-fixture\r\n', encoding='utf-8')
        with patch.dict(os.environ, {'ORACLE_CONTRASENA_FILE': str(archivo)}):
            self.assertEqual(obtener_configuracion('ORACLE_CONTRASENA'), 'secreto-fixture')
            with patch.dict(os.environ, {'ORACLE_CONTRASENA': ''}):
                self.assertEqual(obtener_configuracion('ORACLE_CONTRASENA'), '')
        archivo.unlink()
        with patch.dict(os.environ, {'ORACLE_CONTRASENA_FILE': str(archivo)}):
            with self.assertRaisesRegex(ValueError, '^No se pudo leer el archivo privado de ORACLE_CONTRASENA.$'):
                obtener_configuracion('ORACLE_CONTRASENA')

    def test_tls_y_arranque_sin_alterar_el_tema_local(self):
        self.assertEqual(validar_configuracion(), 'aula.example.com')
        self.assertTrue(parametros_transporte()['ssl_server_dn_match'])
        comando = comando_streamlit('aula.example.com')
        self.assertIn('--server.enableXsrfProtection=true', comando)
        self.assertIn('--server.enableCORS=true', comando)
        self.assertIn('--server.fileWatcherType=none', comando)
        self.assertIn('--browser.serverAddress=aula.example.com', comando)
        self.assertFalse(any('theme.' in s for s in comando))

    def test_urls_y_cuentas_inadecuadas_se_rechazan(self):
        for url in ('http://aula.example.com', 'https://localhost:8501', 'https://127.0.0.1',
                    'https://aula.example.com/portal', 'https://user:pass@aula.example.com',
                    'https://aula.example.com?x=1', 'https://aula.example.com:8443',
                    'https://aula.example.com:99999', 'https://aula.local'):
            with self.subTest(url=url), patch.dict(self.config, {'APP_BASE_URL': url}), self.assertRaises(ValueError):
                validar_configuracion()
        for usuario in ('ADMIN', 'SYS', 'SYSTEM', 'UPC_AULA_APP', 'UPC_ASISTENCIA'):
            with self.subTest(usuario=usuario), patch.dict(self.config, {'ORACLE_ADMIN_USUARIO': usuario}), self.assertRaises(ValueError):
                validar_configuracion()

    def test_clave_base64_conserva_huella_y_validacion_del_arranque(self):
        from src.servicios.verificacion_identidad import huella_documento
        original = bytes(range(32))
        self.clave.write_bytes(original)
        esperado = huella_documento('CC', '12345678')
        texto = self.ruta / 'identidad.key.b64'
        texto.write_bytes(base64.b64encode(original) + b'\r\n')
        with patch.dict(self.config, {'IDENTIDAD_CLAVE_RUTA': str(texto), 'IDENTIDAD_CLAVE_FORMATO': 'base64'}):
            self.assertEqual(validar_configuracion(), 'aula.example.com')
            self.assertEqual(huella_documento('CC', '12345678'), esperado)
        self.assertEqual(self.clave.read_bytes(), original)

    def test_clave_base64_invalida_bloquea_el_arranque_sin_exponerla(self):
        from src.servicios.verificacion_identidad import huella_documento
        texto = self.ruta / 'identidad.key.b64'
        for contenido in (b'privado-fixture-no-base64!', base64.b64encode(b'x' * 31)):
            texto.write_bytes(contenido)
            with self.subTest(contenido=contenido), patch.dict(self.config, {
                    'IDENTIDAD_CLAVE_RUTA': str(texto), 'IDENTIDAD_CLAVE_FORMATO': 'base64'}):
                with self.assertRaises(ValueError) as salida:
                    validar_configuracion()
                self.assertNotIn(contenido.decode('ascii'), str(salida.exception))
                with self.assertRaises(ValueError):
                    huella_documento('CC', '12345678')
        with patch.dict(self.config, {'IDENTIDAD_CLAVE_FORMATO': 'desconocido'}), self.assertRaises(ValueError):
            validar_configuracion()

    def test_clave_base64_ausente_no_se_regenera(self):
        from src.servicios.verificacion_identidad import preparar_clave
        ausente = self.ruta / 'no-crear.key.b64'
        with patch.dict(self.config, {'IDENTIDAD_CLAVE_RUTA': str(ausente), 'IDENTIDAD_CLAVE_FORMATO': 'base64'}), \
                patch('src.servicios.verificacion_identidad.obtener_conexion') as conectar, \
                self.assertRaisesRegex(ValueError, 'original'):
            preparar_clave()
        conectar.assert_not_called()
        self.assertFalse(ausente.exists())

    def test_no_inventa_clave_ni_admite_pool_invalido(self):
        self.clave.unlink()
        with self.assertRaisesRegex(ValueError, 'clave de identidad original'):
            validar_configuracion()
        self.assertFalse(self.clave.exists())
        self.clave.write_bytes(b'x' * 31)
        with self.assertRaisesRegex(ValueError, '32 bytes'):
            validar_configuracion()
        self.clave.write_bytes(b'x' * 32)
        with patch.dict(self.config, {'ORACLE_ADMIN_POOL_MAXIMO': 0}):
            with self.assertRaisesRegex(ValueError, 'ORACLE_ADMIN_POOL'):
                validar_configuracion()

    def test_rechaza_tcp_incluso_en_descriptores_con_varias_direcciones(self):
        dsn = ('(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=TCPS)(HOST=db.example.com)(PORT=1522))'
               '(ADDRESS=(PROTOCOL=TCP)(HOST=otro.example.com)(PORT=1521)))'
               '(CONNECT_DATA=(SERVICE_NAME=servicio_low)))')
        for valor in (dsn, 'db.example.com:1521/svc',
                      'tcps://db.example.com:1522/svc?ssl_server_dn_match=no'):
            with self.subTest(dsn=valor), patch.dict(self.config, {'ORACLE_DSN': valor}), self.assertRaisesRegex(ValueError, 'TCPS'):
                parametros_transporte()
        with patch.dict(self.config, {'ORACLE_TLS_MODO': 'local'}):
            self.assertEqual(parametros_transporte(), {})
            with self.assertRaisesRegex(ValueError, 'debe ser tls o mtls'):
                validar_configuracion()

    def test_wallet_resuelve_alias_y_conserva_verificacion_del_servidor(self):
        (self.ruta / 'tnsnames.ora').write_text('aula_low=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCPS)'
            '(HOST=db.example.com)(PORT=1522))(CONNECT_DATA=(SERVICE_NAME=svc)))', encoding='utf-8')
        (self.ruta / 'ewallet.pem').write_text('fixture-no-es-un-wallet', encoding='utf-8')
        with patch.dict(self.config, {'ORACLE_TLS_MODO': 'mtls', 'ORACLE_DSN': 'aula_low',
                'ORACLE_WALLET_DIRECTORIO': str(self.ruta), 'ORACLE_WALLET_CONTRASENA': 'fixture'}):
            opciones = parametros_transporte()
            self.assertEqual(opciones['config_dir'], str(self.ruta))
            self.assertEqual(opciones['wallet_location'], str(self.ruta))
            self.assertTrue(opciones['ssl_server_dn_match'])
            self.assertEqual(validar_configuracion(), 'aula.example.com')
            (self.ruta / 'ewallet.pem').unlink()
            with self.assertRaisesRegex(ValueError, 'ewallet.pem'):
                parametros_transporte()

    def test_ambos_pools_reciben_el_transporte_cloud(self):
        from src.base_datos import configuracion, administracion
        with patch.object(configuracion, '_grupo_conexiones', None), \
                patch.object(configuracion, 'ORACLE_CONTRASENA', 'fixture'), \
                patch.object(administracion, '_pool', None), \
                patch('oracledb.create_pool') as crear:
            configuracion.obtener_pool()
            administracion.obtener_pool_admin()
            self.assertEqual(crear.call_count, 2)
            for llamada in crear.call_args_list:
                self.assertIs(llamada.kwargs['ssl_server_dn_match'], True)

    def test_preflight_base_es_de_solo_lectura_y_revisa_permisos(self):
        propietario = MagicMock()
        consulta = propietario.__enter__.return_value.cursor.return_value.__enter__.return_value
        consulta.__iter__.return_value = iter([(f'{n:03d}',) for n in range(1, 10)])
        consulta.fetchone.side_effect = [('UPC_AULA_APP', 'UPC_ASISTENCIA'), (0,), (0,)]
        from src.base_datos.permisos_ejecucion import contrato_permisos
        contrato = contrato_permisos()
        consulta.fetchall.side_effect = [[], [],
            [(o, p, 'NO') for o, p, c in contrato if c is None],
            [(o, c, p, 'NO') for o, p, c in contrato if c is not None]]
        limitada = MagicMock()
        limitada.acquire.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value.fetchone.return_value = (5,)
        with patch('src.base_datos.configuracion.obtener_conexion', return_value=propietario), \
                patch('src.base_datos.administracion.obtener_pool_admin', return_value=limitada):
            comprobar_base()
        for cursor in (consulta, limitada.acquire.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value):
            for llamada in cursor.execute.call_args_list:
                self.assertTrue(llamada.args[0].lstrip().upper().startswith('SELECT'))
        propietario.commit.assert_not_called()

    def test_alta_inicial_no_reemplaza_cuentas_ni_escribe_sin_validar(self):
        import sys
        import importlib
        with patch.object(sys, 'path', [str(Path(__file__).resolve().parents[1] / 'scripts'), *sys.path]):
            herramienta = importlib.import_module('crear_administrador')
        conexion = MagicMock()
        cur = conexion.__enter__.return_value.cursor.return_value.__enter__.return_value
        cur.fetchone.return_value = (1,)
        with patch.dict(self.config, {'ORACLE_USUARIO': 'UPC_ASISTENCIA'}), \
                patch('src.base_datos.configuracion.obtener_conexion', return_value=conexion), \
                patch('src.servicios.seguridad_claves.evaluar_clave', return_value=MagicMock(puntuacion=4)):
            with self.assertRaisesRegex(ValueError, 'Ya existe'):
                herramienta.crear_cuenta('admin.fixture', 'Cuenta de prueba', 'credencial-de-fixture-no-utilizable')
        self.assertEqual(cur.execute.call_count, 1)
        conexion.__enter__.return_value.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
