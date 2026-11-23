import importlib
import json
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from _scripts_sql import leer_script, ejecutar_script
cloud = importlib.import_module('preparar_oracle_cloud')


class LectorSQLTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)

    def test_inclusiones_relativas_y_bloques_no_se_dividen_por_punto_y_coma(self):
        (self.raiz / 'sql').mkdir()
        (self.raiz / 'entrada.sql').write_text('@sql/uno.sql\n', encoding='utf-8')
        (self.raiz / 'sql/uno.sql').write_text('SET DEFINE OFF\n@@dos.sql\nSELECT 1\nFROM dual;\n', encoding='utf-8')
        (self.raiz / 'sql/dos.sql').write_text("DECLARE n NUMBER;\nBEGIN\nEXECUTE IMMEDIATE q'~CREATE TABLE fixture(n NUMBER);~';\nEND;\n/\n", encoding='utf-8')
        plan = list(leer_script(self.raiz / 'entrada.sql', self.raiz))
        self.assertEqual(len(plan), 2)
        self.assertTrue(plan[0].sql.startswith('DECLARE'))
        self.assertTrue(plan[0].sql.endswith('END;'))
        self.assertEqual(plan[1].sql, 'SELECT 1\nFROM dual')

    def test_rechaza_ciclos_escape_directivas_no_soportadas_y_bloques_incompletos(self):
        archivo = self.raiz / 'entrada.sql'
        for contenido in ('@@entrada.sql\n', '@../ajeno.sql\n', 'CONNECT usuario\n',
                          'SET DEFINE ON\n', 'BEGIN\nNULL;\nEND;\n', 'SELECT 1 FROM dual\n'):
            with self.subTest(contenido=contenido):
                archivo.write_text(contenido, encoding='utf-8')
                with self.assertRaises(ValueError):
                    list(leer_script(archivo, self.raiz))

    def test_error_informa_archivo_y_linea_sin_repetir_sql(self):
        archivo = self.raiz / 'entrada.sql'
        archivo.write_text("SELECT 'fixture-no-publicar' FROM dual;\n", encoding='utf-8')
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value.execute.side_effect = Exception('fixture-no-publicar')
        with self.assertRaises(RuntimeError) as error:
            ejecutar_script(conn, leer_script(archivo, self.raiz))
        self.assertIn('entrada.sql:1', str(error.exception))
        self.assertNotIn('fixture-no-publicar', str(error.exception))

    def test_instalador_real_incluye_las_once_versiones_y_sus_verificadores(self):
        plan = list(leer_script(cloud.RAIZ / 'oracle_scripts.sql', cloud.RAIZ))
        archivos = {s.archivo.name for s in plan}
        self.assertTrue({'01_tablas.sql', '008_excepciones.sql', '35_verificar_excepciones.sql',
                         '28_paquete_administracion.sql', '32_paquete_sesiones.sql',
                         '011_documento_estudiantil.sql', '45_verificar_documentos.sql'} <= archivos)
        self.assertEqual(len([s for s in plan if s.sql.upper().startswith('COMMIT')]), 11)
        self.assertTrue(all(s.sql.strip() and not s.sql.startswith('@') for s in plan))

    def test_cada_migracion_recompila_antes_de_verificar_y_registrar_version(self):
        for numero, nombre in cloud.MIGRACIONES:
            with self.subTest(version=numero):
                plan = list(leer_script(cloud.RAIZ / 'sql/migraciones' / nombre, cloud.RAIZ))
                recompilacion = next(i for i, s in enumerate(plan) if s.archivo.name == '36_recompilar_esquema.sql')
                verificacion = next(i for i, s in enumerate(plan) if s.archivo.name in
                    {'04_verificar.sql', '33_verificar_sesiones.sql', '35_verificar_excepciones.sql', '39_verificar_excepciones_docentes.sql', '40_verificar_prueba_academica.sql', '45_verificar_documentos.sql'})
                registro = next(i for i, s in enumerate(plan) if s.sql.upper().startswith('INSERT INTO VERSIONES_ESQUEMA'))
                self.assertLess(recompilacion, verificacion)
                self.assertLess(verificacion, registro)


class PreparacionCloudTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.carpeta = Path(self.temporal.name)
        self.archivo = self.carpeta / 'credenciales_tecnicas.toml'
        (self.carpeta / 'dsn.txt').write_text('tcps://adb.us-ashburn-1.oraclecloud.com:1522/fixture_low.adb.oraclecloud.com', encoding='utf-8')
        for objeto, nombre, valor in ((cloud, 'CARPETA', self.carpeta), (cloud, 'CUENTAS', self.archivo),
                                      (sys, 'argv', ['preparar_oracle_cloud.py'])):
            parche = patch.object(objeto, nombre, valor)
            parche.start(); self.addCleanup(parche.stop)
        for nombre, valor in (('usar_entorno', None), ('getpass', 'fixture-admin-no-guardar')):
            parche = patch.object(cloud, nombre, return_value=valor)
            parche.start(); self.addCleanup(parche.stop)
        parche = patch.object(sys.stdin, 'isatty', return_value=True)
        parche.start(); self.addCleanup(parche.stop)

    def test_no_reemplaza_usuarios_existentes_ni_genera_credenciales(self):
        conn = MagicMock()
        cursor = conn.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [('UPC_ASISTENCIA',)]
        with patch.object(cloud.oracledb, 'connect', return_value=conn):
            with self.assertRaisesRegex(SystemExit, 'Ya existe una cuenta'):
                cloud.main()
        self.assertFalse(self.archivo.exists())
        self.assertEqual(cursor.execute.call_count, 1)

    def test_conserva_claves_antes_del_ddl_y_no_guarda_admin(self):
        conn = MagicMock()
        cursor = conn.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []

        def ejecutar(sql, **binds):
            if binds:
                config = tomllib.loads(self.archivo.read_text(encoding='utf-8'))
                self.assertEqual(config['ORACLE_CONTRASENA'], binds['clave_propietario'])
                self.assertEqual(config['ORACLE_ADMIN_CONTRASENA'], binds['clave_administracion'])
                self.assertNotIn('fixture-admin-no-guardar', self.archivo.read_text(encoding='utf-8'))
                raise RuntimeError('Fallo simulado de DDL; conservar estado.')
        cursor.execute.side_effect = ejecutar
        with patch.object(cloud.oracledb, 'connect', return_value=conn):
            with self.assertRaisesRegex(SystemExit, 'Fallo simulado'):
                cloud.main()
        self.assertTrue(self.archivo.exists())
        self.assertEqual(json.loads((self.carpeta / 'instalacion.json').read_text())['fase'], 'creacion_usuarios_iniciada')

    def test_no_repite_una_preparacion_con_credenciales_ya_guardadas(self):
        self.archivo.write_text('# fixture\n', encoding='utf-8')
        with patch.object(cloud.oracledb, 'connect') as conectar:
            with self.assertRaisesRegex(SystemExit, 'Ya hay credenciales'):
                cloud.main()
        conectar.assert_not_called()

    def test_continuacion_solo_selecciona_versiones_no_aplicadas(self):
        pendientes = cloud.migraciones_pendientes({'001', '002', '003'})
        self.assertEqual([n for n, _ in pendientes], ['004', '005', '006', '007', '008', '009', '010', '011'])
        self.assertEqual(cloud.migraciones_pendientes({f'{n:03d}' for n in range(1, 12)}), [])
        for versiones in (set(), {'002'}, {'001', '003'}, {'001', '009'}):
            with self.subTest(versiones=versiones), self.assertRaises(ValueError):
                cloud.migraciones_pendientes(versiones)

    def test_continuacion_no_recrea_cuentas_ni_ejecuta_001(self):
        config = {'ORACLE_USUARIO': 'UPC_ASISTENCIA', 'ORACLE_CONTRASENA': 'fixture',
                  'ORACLE_ADMIN_USUARIO': 'UPC_ADMIN_APP', 'ORACLE_ADMIN_CONTRASENA': 'fixture-limitada',
                  'ORACLE_DSN': (self.carpeta / 'dsn.txt').read_text()}
        (self.carpeta / 'instalacion.json').write_text('{"fase":"instalacion_iniciada"}', encoding='utf-8')
        conn = MagicMock()
        conn.__enter__.return_value.cursor.return_value.__enter__.return_value.fetchall.return_value = [('001',)]
        with patch.object(cloud.oracledb, 'connect', return_value=conn) as conectar, \
                patch.object(cloud, 'ejecutar_script') as ejecutar, patch.object(cloud, 'verificar') as verificar:
            cloud.continuar(MagicMock(), config)
        conectar.assert_called_once()
        self.assertEqual(conectar.call_args.kwargs['user'], 'UPC_ASISTENCIA')
        for llamada in ejecutar.call_args_list:
            for sentencia in llamada.args[1]:
                self.assertNotEqual(sentencia.archivo.name, '01_tablas.sql')
                self.assertNotIn('CREATE USER', sentencia.sql.upper())
        verificar.assert_called_once()

    def test_continuacion_recupera_permisos_si_011_ya_quedo_registrada(self):
        config = {'ORACLE_USUARIO': 'UPC_ASISTENCIA', 'ORACLE_CONTRASENA': 'fixture',
                  'ORACLE_ADMIN_USUARIO': 'UPC_ADMIN_APP', 'ORACLE_ADMIN_CONTRASENA': 'fixture-limitada',
                  'ORACLE_DSN': (self.carpeta / 'dsn.txt').read_text()}
        (self.carpeta / 'instalacion.json').write_text('{"fase":"migracion_en_curso","version":"011"}', encoding='utf-8')
        conn = MagicMock()
        conn.__enter__.return_value.cursor.return_value.__enter__.return_value.fetchall.return_value = [(f'{n:03d}',) for n in range(1, 12)]
        with patch.object(cloud.oracledb, 'connect', return_value=conn), \
                patch.object(cloud, 'ejecutar_script') as ejecutar, patch.object(cloud, 'verificar'):
            cloud.continuar(MagicMock(), config)
        ejecutar.assert_called_once()
        self.assertEqual({s.archivo.name for s in ejecutar.call_args.args[1]}, {'01_permisos_administracion.sql'})

    def test_destino_distinto_se_rechaza_antes_de_conectar(self):
        for usuario, dsn in (('ADMIN', (self.carpeta / 'dsn.txt').read_text()),
                             ('UPC_ASISTENCIA', 'localhost:1521/XEPDB1')):
            config = {'ORACLE_USUARIO': usuario, 'ORACLE_ADMIN_USUARIO': 'UPC_ADMIN_APP', 'ORACLE_DSN': dsn}
            with self.subTest(usuario=usuario, dsn=dsn), patch.object(cloud.oracledb, 'connect') as conectar:
                with self.assertRaises(ValueError):
                    cloud.continuar(MagicMock(), config)
                conectar.assert_not_called()


if __name__ == '__main__':
    unittest.main()
