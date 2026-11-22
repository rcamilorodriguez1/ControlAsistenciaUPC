"""Ensayo opt-in con usuario temporal limitado; todos los datos terminan en rollback."""
import json
import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch
from uuid import uuid4


@unittest.skipUnless(os.environ.get('UPC_TEST_EJECUCION_CONFIG'), 'Requiere un perfil privado de cuenta temporal limitada.')
class EjecucionOracleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import oracledb
        cls.oracledb = oracledb
        cls.config = json.loads(Path(os.environ['UPC_TEST_EJECUCION_CONFIG']).read_text(encoding='utf-8'))
        if not re.fullmatch(r'UPC_RUN_[A-F0-9]{8}', cls.config['ORACLE_USUARIO']):
            raise ValueError('El ensayo exige un usuario temporal con prefijo UPC_RUN_.')

    def setUp(self):
        self.conn = self.oracledb.connect(user=self.config['ORACLE_USUARIO'],
            password=self.config['ORACLE_CONTRASENA'], dsn=self.config['ORACLE_DSN'])
        self.conn.current_schema = self.config['ORACLE_ESQUEMA']
        self.tablas = ('profesores', 'estudiantes', 'materias', 'materia_estudiantes',
            'clases', 'registros_asistencia', 'verificacion_estudiantes', 'sesiones_usuario', 'limites_acceso')
        self.antes = self.contar()
        self.addCleanup(self.cerrar)

    def contar(self):
        with self.conn.cursor() as cur:
            resultado = {}
            for tabla in self.tablas:
                cur.execute('SELECT COUNT(*) FROM ' + tabla)
                resultado[tabla] = cur.fetchone()[0]
            return resultado

    def cerrar(self):
        try:
            self.conn.rollback()
            self.assertEqual(self.contar(), self.antes, 'No deben persistir filas del ensayo.')
        finally:
            self.conn.close()

    def test_identidad_privilegios_y_contrato_exacto(self):
        from src.base_datos.permisos_ejecucion import comprobar_permisos
        from pathlib import Path
        raiz = Path(__file__).resolve().parents[1]
        with self.conn.cursor() as cur:
            # Únicamente sustituir el nombre fijo por el identificador temporal validado.
            verificador = (raiz / 'sql/cloud/08_verificar_ejecucion.sql').read_text(encoding='utf-8')
            cur.execute(verificador.rstrip().removesuffix('/').rstrip().replace('UPC_AULA_APP', self.config['ORACLE_USUARIO']))
            self.assertEqual(comprobar_permisos(cur, self.config['ORACLE_ESQUEMA']), 53)
            cur.execute('SELECT USER, SYS_CONTEXT(\'USERENV\',\'CURRENT_SCHEMA\') FROM dual')
            self.assertEqual(cur.fetchone(), (self.config['ORACLE_USUARIO'], self.config['ORACLE_ESQUEMA']))

    def test_catalogo_runtime_analiza_sin_ejecutar_ddl_ni_dml(self):
        raiz = Path(__file__).resolve().parents[1] / 'sql/consultas'
        with self.conn.cursor() as cur:
            for carpeta in ['base_datos/bd', 'base_datos/clases', 'base_datos/perfil_estudiante',
                    'base_datos/administracion', 'servicios/recuperacion_acceso',
                    'servicios/verificacion_identidad', 'servicios/sesiones_servidor', 'compartidas']:
                for archivo in sorted((raiz / carpeta).glob('*.sql')):
                    sql = archivo.read_text(encoding='utf-8')
                    if '{' not in sql and re.match(r'\s*(SELECT|WITH|INSERT|UPDATE|DELETE|BEGIN)\b', sql, re.I):
                        with self.subTest(archivo=str(archivo.relative_to(raiz))):
                            cur.parse(sql)

    def test_escrituras_reservadas_son_denegadas_sin_tocar_filas(self):
        consultas = [
            'DELETE FROM profesores WHERE 1=0',
            'UPDATE profesores SET activo=0 WHERE 1=0',
            'INSERT INTO administradores(usuario,nombre,contrasena) SELECT NULL,NULL,NULL FROM dual WHERE 1=0',
            'UPDATE administradores SET activo=0 WHERE 1=0',
            'DELETE FROM eventos_gestion WHERE 1=0',
            'DELETE FROM auditoria_asistencia WHERE 1=0',
            'DELETE FROM historial_matriculas WHERE 1=0',
            "UPDATE verificacion_estudiantes SET excepcion_activa=1 WHERE 1=0",
        ]
        with self.conn.cursor() as cur:
            for sql in consultas:
                with self.subTest(operacion=sql.split()[0], objeto=sql.split()[2]):
                    with self.assertRaises(self.oracledb.DatabaseError) as error:
                        cur.execute(sql)
                    self.assertIn(error.exception.args[0].code, (942, 1031))
            with self.assertRaises(self.oracledb.DatabaseError):
                cur.callproc('pkg_administracion.cuentas', ['PROFESOR', None, cur])
            with self.assertRaises(self.oracledb.DatabaseError):
                cur.callproc('pkg_excepciones.revocar', [0, 0, 'Fixture'])

    def test_clase_matricula_sesion_y_perfil_con_cuenta_limitada(self):
        from src.base_datos.consultas import cargar_sql
        codigo = 'RUN_' + uuid4().hex[:16]
        with self.conn.cursor() as cur:
            def insertar(consulta, **kw):
                salida = cur.var(self.oracledb.NUMBER)
                cur.execute(cargar_sql(consulta), out_id=salida, **kw)
                return int(salida.getvalue()[0])
            profesor = insertar('base_datos/bd/crear_profesor_01', usuario=codigo,
                contrasena='FIXTURE_NO_UTILIZABLE', nombre='Docente sintético de ejecución')
            estudiante = insertar('base_datos/bd/crear_estudiante_01', nombre='Estudiante sintético de ejecución',
                codigo_institucional=codigo, embedding_facial=json.dumps([0.1] * 128), embedding_voz=None)
            cur.callproc('pkg_sesiones.abrir', ['PROFESOR', profesor, 'a' * 64])
            cur.callproc('pkg_sesiones.validar', ['PROFESOR', profesor, 'a' * 64, 1])
            cur.callproc('pkg_auditoria.establecer_contexto', ['PROFESOR', profesor, None])
            materia = cur.var(self.oracledb.NUMBER)
            cur.callproc('pkg_gestion.crear_materia', [codigo, 'Materia sintética', 'RUN', materia])
            materia = int(materia.getvalue())
            cur.callproc('pkg_gestion.matricular', [estudiante, materia])
            clase = cur.var(self.oracledb.NUMBER)
            cur.execute(cargar_sql('base_datos/clases/abrir_clase_01'),
                m=materia, f='2026-11-21T10:00:00.000000-05:00', id=clase)
            clase = int(clase.getvalue())
            cantidad = cur.var(self.oracledb.NUMBER)
            propuesta = json.dumps([{'estudiante_id': estudiante, 'detectado': 1,
                'estado_deteccion': 'PRESENTE', 'presente': 1, 'motivo': None,
                'fecha_hora': '2026-11-21T10:01:00.000000-05:00'}])
            cur.execute(cargar_sql('base_datos/clases/confirmar_clase_02'),
                c=clase, clave=uuid4().hex, origen='FACIAL', carga=propuesta, n=cantidad)
            self.assertEqual(cantidad.getvalue(), 1)
            cur.callproc('pkg_auditoria.establecer_contexto', ['ESTUDIANTE', estudiante, None])
            cur.execute(cargar_sql('base_datos/perfil_estudiante/operacion_02'), estudiante_id=estudiante)
            self.assertEqual(len(cur.fetchall()), 1)
            cur.callproc('pkg_sesiones.cerrar', ['PROFESOR', profesor, 'a' * 64])

    def test_preflight_real_y_pool_reutilizado_resuelven_propietario(self):
        from src.base_datos import configuracion, esquema
        from src.servicios.despliegue import comprobar_base
        entorno = {'ORACLE_USUARIO': self.config['ORACLE_USUARIO'], 'ORACLE_ESQUEMA': self.config['ORACLE_ESQUEMA']}
        with patch.dict(os.environ, entorno):
            pool = self.oracledb.create_pool(user=self.config['ORACLE_USUARIO'],
                password=self.config['ORACLE_CONTRASENA'], dsn=self.config['ORACLE_DSN'],
                min=0, max=1, increment=1, session_callback=esquema.iniciar_sesion)
            try:
                with patch.object(configuracion, 'obtener_pool', return_value=pool):
                    with configuracion.obtener_conexion() as conn:
                        conn.current_schema = self.config['ORACLE_USUARIO']
                        with conn.cursor() as cur:
                            cur.execute('SELECT 1 FROM dual')
                    comprobar_base()
            finally:
                pool.close()
