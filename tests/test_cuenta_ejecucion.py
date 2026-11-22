import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import MagicMock, patch

from src.base_datos import esquema, permisos_ejecucion, configuracion, administracion, recuperacion


class EsquemaTest(unittest.TestCase):
    def test_resuelve_propietario_sin_confundirlo_con_usuario(self):
        with patch.dict(os.environ, {'ORACLE_USUARIO': 'UPC_AULA_APP', 'ORACLE_ESQUEMA': 'upc_asistencia'}):
            self.assertEqual(esquema.esquema_propietario(), 'UPC_ASISTENCIA')
            self.assertEqual(administracion.propietario(), '"UPC_ASISTENCIA"')
            conn = MagicMock()
            esquema.iniciar_sesion(conn)
            self.assertEqual(conn.current_schema, 'UPC_ASISTENCIA')
            conn.cursor.assert_not_called()

    def test_instalacion_local_anterior_conserva_su_propietario(self):
        with patch.dict(os.environ, {'ORACLE_USUARIO': 'UPC_ASISTENCIA'}), \
                patch('src.base_datos.esquema.obtener_configuracion', side_effect=lambda k, d=None: 'UPC_ASISTENCIA' if k == 'ORACLE_USUARIO' else d):
            self.assertEqual(esquema.esquema_propietario(), 'UPC_ASISTENCIA')

    def test_rechaza_identificadores_antes_de_abrir_pool(self):
        for valor in ('UPC; DROP USER X', 'UPC.OTRO', ' UPC', '', None, 'X' * 31):
            with self.subTest(valor=valor), patch('src.base_datos.esquema.obtener_configuracion', return_value=valor), \
                    patch.object(configuracion, '_grupo_conexiones', None), \
                    patch.object(configuracion, 'ORACLE_CONTRASENA', 'fixture'), \
                    patch('oracledb.create_pool') as crear:
                with self.assertRaises(ValueError):
                    configuracion.obtener_pool()
                crear.assert_not_called()

    def test_adquisicion_restauracion_de_esquema_y_descarte_si_falla(self):
        pool = MagicMock()
        with patch.object(configuracion, 'obtener_pool', return_value=pool), \
                patch.object(configuracion, 'iniciar_sesion') as iniciar:
            self.assertIs(configuracion.obtener_conexion(), pool.acquire.return_value)
            iniciar.assert_called_once_with(pool.acquire.return_value)
            iniciar.side_effect = ValueError('fixture')
            with self.assertRaises(ValueError):
                configuracion.obtener_conexion()
            pool.drop.assert_called_once_with(pool.acquire.return_value)

    def test_respaldo_con_runtime_no_crea_copia_vacia(self):
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value.fetchone.return_value = ('UPC_AULA_APP', 'UPC_ASISTENCIA')
        with tempfile.TemporaryDirectory() as directorio:
            destino = Path(directorio) / 'no-crear'
            with self.assertRaises(PermissionError):
                recuperacion.respaldar(conn, destino, b'x' * 32)
            self.assertFalse(destino.exists())


class PermisosTest(unittest.TestCase):
    def setUp(self):
        self.contrato = permisos_ejecucion.contrato_permisos()
        self.objetos = [(o, p, 'NO') for o, p, c in self.contrato if c is None]
        self.columnas = [(o, c, p, 'NO') for o, p, c in self.contrato if c is not None]

    def test_contrato_no_concede_administracion_ni_cambios_al_historial(self):
        self.assertNotIn(('ADMINISTRADORES', 'INSERT', None), self.contrato)
        for objeto in ('PKG_ADMINISTRACION', 'PKG_EXCEPCIONES', 'AUDITORIA_ASISTENCIA', 'HISTORIAL_MATRICULAS'):
            self.assertFalse(any(o == objeto for o, _, _ in self.contrato))
        self.assertEqual({c for o, p, c in self.contrato if o == 'PROFESORES' and p == 'UPDATE'}, {'CONTRASENA'})

    def test_detecta_faltantes_excesos_y_grant_option(self):
        for objetos, columnas in ((self.objetos[:-1], self.columnas),
                (self.objetos + [('PROFESORES', 'DELETE', 'NO')], self.columnas),
                (self.objetos, self.columnas + [('PROFESORES', 'ACTIVO', 'UPDATE', 'NO')]),
                ([(o, p, 'YES') for o, p, _ in self.objetos], self.columnas)):
            cur = MagicMock()
            cur.fetchall.side_effect = [objetos, columnas]
            with self.assertRaises(ValueError):
                permisos_ejecucion.comprobar_permisos(cur, 'UPC_ASISTENCIA')
        cur = MagicMock()
        cur.fetchall.side_effect = [self.objetos, self.columnas]
        self.assertEqual(permisos_ejecucion.comprobar_permisos(cur, 'UPC_ASISTENCIA'), len(self.contrato))


class ProvisionEjecucionTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
        self.herramienta = importlib.import_module('preparar_ejecucion_cloud')
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.carpeta = Path(self.temporal.name)
        self.dsn = 'tcps://adb.us-ashburn-1.oraclecloud.com:1522/fixture_low.adb.oraclecloud.com'
        (self.carpeta / 'dsn.txt').write_text(self.dsn, encoding='utf-8')
        self.propietario = {'ORACLE_USUARIO': 'UPC_ASISTENCIA', 'ORACLE_CONTRASENA': 'clave-propietario-fixture',
            'ORACLE_ADMIN_USUARIO': 'UPC_ADMIN_APP', 'ORACLE_ADMIN_CONTRASENA': 'clave-admin-fixture',
            'ORACLE_DSN': self.dsn, 'ORACLE_TLS_MODO': 'tls'}
        archivo = self.carpeta / 'credenciales_tecnicas.toml'
        archivo.write_text('\n'.join(k + ' = ' + json.dumps(v) for k, v in self.propietario.items()), encoding='utf-8')
        for nombre, valor in [('CARPETA', self.carpeta), ('CUENTAS', archivo), ('EJECUCION', self.carpeta / 'ejecucion.toml')]:
            parche = patch.object(self.herramienta, nombre, valor)
            parche.start(); self.addCleanup(parche.stop)
        parche = patch.object(self.herramienta, 'usar_entorno')
        parche.start(); self.addCleanup(parche.stop)

    def test_perfil_es_exclusivo_y_no_contiene_clave_propietaria(self):
        config = self.herramienta.guardar_cuenta(self.propietario)
        self.herramienta.validar_destino(config, ejecucion=True)
        contenido = self.herramienta.EJECUCION.read_text(encoding='utf-8')
        self.assertNotIn(self.propietario['ORACLE_CONTRASENA'], contenido)
        self.assertEqual(tomllib.loads(contenido)['ORACLE_USUARIO'], 'UPC_AULA_APP')
        with self.assertRaises(FileExistsError):
            self.herramienta.guardar_cuenta(self.propietario)
        with self.assertRaises(ValueError):
            self.herramienta.validar_destino({**config, 'ORACLE_DSN': 'localhost:1521/XEPDB1'}, ejecucion=True)

    def test_plan_no_usa_red_ni_admin(self):
        with patch.object(sys, 'argv', ['preparar_ejecucion_cloud.py', '--comprobar-plan']), \
                patch.object(self.herramienta.oracledb, 'connect') as conectar, \
                patch.object(self.herramienta, 'getpass') as clave:
            self.herramienta.main()
            conectar.assert_not_called(); clave.assert_not_called()

    def test_preparacion_ya_existente_no_reemplaza_ni_pide_admin(self):
        self.herramienta.guardar_cuenta(self.propietario)
        with patch.object(sys, 'argv', ['preparar_ejecucion_cloud.py']), \
                patch.object(self.herramienta.oracledb, 'connect') as conectar, \
                patch.object(self.herramienta, 'getpass') as clave, \
                self.assertRaisesRegex(SystemExit, 'Ya hay credenciales'):
            self.herramienta.main()
        conectar.assert_not_called(); clave.assert_not_called()

    def test_continuacion_autentica_antes_de_conceder(self):
        self.herramienta.guardar_cuenta(self.propietario)
        with patch.object(sys, 'argv', ['preparar_ejecucion_cloud.py', '--continuar']), \
                patch.object(self.herramienta.oracledb, 'connect', side_effect=oracledb_error()) as conectar, \
                patch.object(self.herramienta, 'conceder') as conceder, self.assertRaises(SystemExit):
            self.herramienta.main()
        conceder.assert_not_called()

    def test_cuenta_existente_en_oracle_no_genera_archivo_ni_cambia_clave(self):
        conexion = MagicMock()
        conexion.__enter__.return_value.cursor.return_value.__enter__.return_value.fetchone.return_value = (1,)
        with patch.object(sys, 'argv', ['preparar_ejecucion_cloud.py']), \
                patch.object(sys.stdin, 'isatty', return_value=True), \
                patch.object(self.herramienta, 'getpass', return_value='fixture-admin'), \
                patch.object(self.herramienta.oracledb, 'connect', return_value=conexion), \
                self.assertRaisesRegex(SystemExit, 'ya existe'):
            self.herramienta.main()
        self.assertFalse(self.herramienta.EJECUCION.exists())
        self.assertEqual(conexion.__enter__.return_value.cursor.return_value.__enter__.return_value.execute.call_count, 1)

    def test_creacion_persiste_antes_del_ddl_y_no_guarda_admin(self):
        conexion = MagicMock()
        cur = conexion.__enter__.return_value.cursor.return_value.__enter__.return_value
        cur.fetchone.return_value = (0,)
        def ejecutar(sql, **kw):
            if 'clave_ejecucion' in kw:
                datos = tomllib.loads(self.herramienta.EJECUCION.read_text(encoding='utf-8'))
                self.assertEqual(datos['ORACLE_CONTRASENA'], kw['clave_ejecucion'])
                self.assertNotIn('fixture-admin', self.herramienta.EJECUCION.read_text(encoding='utf-8'))
        cur.execute.side_effect = ejecutar
        with patch.object(sys, 'argv', ['preparar_ejecucion_cloud.py']), \
                patch.object(sys.stdin, 'isatty', return_value=True), \
                patch.object(self.herramienta, 'getpass', return_value='fixture-admin'), \
                patch.object(self.herramienta.oracledb, 'connect', return_value=conexion), \
                patch.object(self.herramienta, 'conceder') as conceder, \
                patch.object(self.herramienta, 'verificar', return_value={'verificado': True}) as verificar:
            self.herramienta.main()
        conceder.assert_called_once()
        verificar.assert_called_once()

    def test_bootstrap_admin_rechaza_runtime_sin_abrir_conexion(self):
        herramienta = importlib.import_module('crear_administrador')
        with patch.dict(os.environ, {'ORACLE_USUARIO': 'UPC_AULA_APP', 'ORACLE_ESQUEMA': 'UPC_ASISTENCIA'}), \
                patch('src.base_datos.configuracion.obtener_conexion') as conectar, \
                self.assertRaisesRegex(ValueError, 'propietario'):
            herramienta.crear_cuenta('admin.fixture', 'Fixture', 'no-se-procesa')
        conectar.assert_not_called()

    def test_admin_rechazado_identifica_fase_y_no_crea_archivos(self):
        import oracledb
        from types import SimpleNamespace
        error = oracledb.DatabaseError(SimpleNamespace(full_code='ORA-01017'))
        with patch.object(sys, 'argv', ['preparar_ejecucion_cloud.py']), \
                patch.object(sys.stdin, 'isatty', return_value=True), \
                patch.object(self.herramienta, 'getpass', return_value='admin-fixture-privado'), \
                patch.object(self.herramienta.oracledb, 'connect', side_effect=error) as conectar, \
                patch.object(self.herramienta, 'conceder') as conceder, self.assertRaises(SystemExit) as salida:
            self.herramienta.main()
        self.assertIn('rechazó el acceso de ADMIN', str(salida.exception))
        self.assertNotIn('admin-fixture-privado', str(salida.exception))
        self.assertFalse(self.herramienta.EJECUCION.exists())
        self.assertEqual(conectar.call_count, 1)
        conceder.assert_not_called()

    def test_continuacion_rechazada_identifica_usuario_sin_pedir_admin(self):
        import oracledb
        from types import SimpleNamespace
        self.herramienta.guardar_cuenta(self.propietario)
        original = self.herramienta.EJECUCION.read_bytes()
        error = oracledb.DatabaseError(SimpleNamespace(full_code='ORA-01017'))
        with patch.object(sys, 'argv', ['preparar_ejecucion_cloud.py', '--continuar']), \
                patch.object(self.herramienta.oracledb, 'connect', side_effect=error), \
                patch.object(self.herramienta, 'getpass') as clave, self.assertRaises(SystemExit) as salida:
            self.herramienta.main()
        self.assertIn('autenticación de UPC_AULA_APP', str(salida.exception))
        self.assertEqual(self.herramienta.EJECUCION.read_bytes(), original)
        clave.assert_not_called()


def oracledb_error():
    import oracledb
    return oracledb.DatabaseError('fixture no utilizable')
