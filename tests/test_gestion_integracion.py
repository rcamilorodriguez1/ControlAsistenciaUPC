import os
import unittest
from unittest.mock import patch
from hashlib import sha256
import uuid

import test_disparadores_integracion as fixtures


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE') == '1', 'Requiere Oracle 005.')
class GestionIntegracionTest(unittest.TestCase):
    limpiar = fixtures.DisparadoresIntegracionTest.limpiar
    contar_tablas = fixtures.DisparadoresIntegracionTest.contar_tablas
    establecer = fixtures.DisparadoresIntegracionTest.establecer
    esperar_error = fixtures.DisparadoresIntegracionTest.esperar_error
    preparar_asistencia = fixtures.DisparadoresIntegracionTest.preparar_asistencia

    def setUp(self):
        fixtures.DisparadoresIntegracionTest.setUp(self)
        self.establecer()

    def test_codigos_y_usuarios_unicos_sin_distinguir_mayusculas(self):
        with self.conn.cursor() as cur:
            cur.execute('SELECT usuario FROM profesores WHERE profesor_id=:p', p=self.profesor)
            usuario = cur.fetchone()[0].lower()
            with self.assertRaises(self.oracledb.IntegrityError):
                cur.execute("INSERT INTO profesores(usuario,contrasena,nombre) VALUES(:u,'fixture','Duplicado')", u=usuario)
            salida = cur.var(self.oracledb.NUMBER)
            cur.execute('SELECT codigo_materia FROM materias WHERE materia_id=:m', m=self.materia)
            codigo = cur.fetchone()[0].lower()
            self.esperar_error(20088, 'pkg_gestion.crear_materia', [codigo, 'Duplicada', 'A', salida])
            codigo = 'TEST-' + uuid.uuid4().hex[:16].upper()
            cur.execute('UPDATE estudiantes SET codigo_institucional=:c WHERE estudiante_id=:e', c=codigo, e=self.estudiante)
            with self.assertRaises(self.oracledb.IntegrityError):
                cur.execute("INSERT INTO estudiantes(nombre,codigo_institucional) VALUES('Duplicado',:c)", c=codigo)

    def test_retiro_y_archivo_conservan_asistencia_y_historial(self):
        asistencia = self.preparar_asistencia()
        with self.conn.cursor() as cur:
            cur.callproc('pkg_gestion.retirar', [self.estudiante, self.materia, 'Cambio de horario'])
            cur.execute('SELECT COUNT(*) FROM registros_asistencia WHERE asistencia_id=:a', a=asistencia)
            self.assertEqual(cur.fetchone()[0], 1)
            cur.callproc('pkg_gestion.matricular', [self.estudiante, self.materia])
            self.establecer('ESTUDIANTE', self.estudiante)
            cur.callproc('pkg_gestion.archivar_estudiante', [self.estudiante, 'Solicitud de cierre'])
            cur.execute('SELECT activo,embedding_facial,embedding_voz FROM estudiantes WHERE estudiante_id=:e', e=self.estudiante)
            self.assertEqual(cur.fetchone(), (0, None, None))
            cur.execute('SELECT COUNT(*) FROM materia_estudiantes WHERE estudiante_id=:e', e=self.estudiante)
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute('SELECT COUNT(*) FROM registros_asistencia WHERE asistencia_id=:a', a=asistencia)
            self.assertEqual(cur.fetchone()[0], 1)
            cur.execute('SELECT COUNT(*) FROM historial_matriculas WHERE estudiante_id=:e', e=self.estudiante)
            self.assertEqual(cur.fetchone()[0], 4)
            cur.execute("SELECT accion,motivo FROM eventos_gestion WHERE entidad_id=:e AND entidad='ESTUDIANTE'", e=self.estudiante)
            self.assertEqual(cur.fetchone(), ('ARCHIVO', 'Solicitud de cierre'))

    def test_archivo_materia_bloquea_nueva_clase_y_matricula(self):
        with self.conn.cursor() as cur:
            self.establecer(actor=self.otro_profesor)
            self.esperar_error(20085, 'pkg_gestion.archivar_materia', [self.materia, 'No autorizado'])
            self.establecer()
            cur.callproc('pkg_gestion.archivar_materia', [self.materia, 'Fin del curso'])
            self.esperar_error(20087, 'pkg_gestion.matricular', [self.estudiante, self.materia])
            with self.assertRaises(self.oracledb.DatabaseError):
                cur.execute('BEGIN pkg_clases.abrir_clase(:m,SYSTIMESTAMP,:s); END;', m=self.materia, s=cur.var(self.oracledb.NUMBER))
            cur.callproc('pkg_gestion.archivar_materia', [self.materia, 'Reintento'])
            cur.execute("SELECT COUNT(*) FROM eventos_gestion WHERE entidad='MATERIA' AND entidad_id=:m", m=self.materia)
            self.assertEqual(cur.fetchone()[0], 1)

    def test_retirar_biometria_exige_cuenta_o_sistema_y_motivo(self):
        self.esperar_error(20085, 'pkg_gestion.retirar_biometria', [self.estudiante, 'Sin permiso'])
        self.establecer('ESTUDIANTE', self.estudiante)
        self.esperar_error(20084, 'pkg_gestion.retirar_biometria', [self.estudiante, ' '])
        with self.conn.cursor() as cur:
            cur.execute("UPDATE estudiantes SET embedding_facial='[1]',embedding_voz='[2]' WHERE estudiante_id=:e", e=self.estudiante)
            cur.callproc('pkg_gestion.retirar_biometria', [self.estudiante, 'Revocar consentimiento'])
            cur.execute('SELECT activo,embedding_facial,embedding_voz FROM estudiantes WHERE estudiante_id=:e', e=self.estudiante)
            self.assertEqual(cur.fetchone(), (1, None, None))

    def test_resumen_activo_y_conteos_no_multiplican_filas_ni_borran_historia(self):
        from src.base_datos import bd
        self.preparar_asistencia()
        with self.conn.cursor() as cur:
            # Una segunda clase y una segunda matrícula no deben multiplicar conteos al unirlas.
            cur.execute("BEGIN pkg_asistencia.registrar_asistencia(:m,:e,SYSTIMESTAMP+INTERVAL '1' DAY,1); END;", m=self.materia, e=self.estudiante)
            segundo = cur.var(self.oracledb.NUMBER)
            cur.execute("INSERT INTO estudiantes(nombre) VALUES('Segundo de prueba') RETURNING estudiante_id INTO :s", s=segundo)
            cur.callproc('pkg_gestion.matricular', [int(segundo.getvalue()[0]), self.materia])
        with patch.object(bd, 'ejecutar_con_reintentos', side_effect=lambda op, **kw: op(self.conn)):
            materia = bd.obtener_materias_profesor(self.profesor)[0]
            self.assertEqual((materia['total_estudiantes'], materia['total_clases']), (2, 2))
            self.assertEqual(bd.obtener_resumen_profesor(self.profesor)['total_materias'], 1)
            with self.conn.cursor() as cur: cur.callproc('pkg_gestion.archivar_materia', [self.materia, 'Cierre de curso'])
            self.assertEqual(bd.obtener_materias_profesor(self.profesor), [])
            resumen = bd.obtener_resumen_profesor(self.profesor)
            self.assertEqual((resumen['total_materias'], resumen['total_estudiantes']), (0, 0))
            alumno = bd.obtener_resumen_estudiante(self.estudiante)
            self.assertEqual((alumno['total_materias'], alumno['total_clases']), (0, 2))

    def test_archivar_docente_desactiva_sus_materias_y_conserva_historia(self):
        asistencia = self.preparar_asistencia()
        self.esperar_error(20085, 'pkg_gestion.archivar_profesor', [self.otro_profesor, 'Otra cuenta'])
        with self.conn.cursor() as cur:
            cur.callproc('pkg_gestion.archivar_profesor', [self.profesor, 'Fin de vinculación'])
            cur.execute('SELECT activo FROM profesores WHERE profesor_id=:p', p=self.profesor)
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute('SELECT activo FROM materias WHERE materia_id=:m', m=self.materia)
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute('SELECT COUNT(*) FROM registros_asistencia WHERE asistencia_id=:a', a=asistencia)
            self.assertEqual(cur.fetchone()[0], 1)
            self.esperar_error(20085, 'pkg_gestion.crear_materia', ['OTRA', 'Curso', 'A', cur.var(self.oracledb.NUMBER)])

    def test_limite_de_intentos_persistente_y_reinicio_tras_exito(self):
        from src.base_datos import bd
        conexion = self.conn
        class SinCommit:
            def cursor(self): return conexion.cursor()
            def commit(self): pass
        with self.conn.cursor() as cur:
            clave = 'ClaveFixture123'
            cur.execute('UPDATE profesores SET contrasena=:h WHERE profesor_id=:p', h=bd.cifrar_contrasena(clave), p=self.profesor)
            cur.execute('SELECT usuario FROM profesores WHERE profesor_id=:p', p=self.profesor)
            usuario = cur.fetchone()[0]
            llave = sha256(usuario.lower().encode()).hexdigest()
            with patch.object(bd, 'ejecutar_con_reintentos', side_effect=lambda op, **kw: op(SinCommit())):
                for _ in range(5): self.assertIsNone(bd.iniciar_sesion_profesor(usuario, 'Incorrecta123'))
                self.assertIsNone(bd.iniciar_sesion_profesor(usuario, clave))
                cur.execute("UPDATE limites_acceso SET ventana_en=SYSTIMESTAMP-INTERVAL '16' MINUTE,bloqueado_hasta=SYSTIMESTAMP-INTERVAL '1' MINUTE WHERE clave=:c", c=llave)
                self.assertEqual(bd.iniciar_sesion_profesor(usuario, clave)['profesor_id'], self.profesor)
                cur.execute('SELECT COUNT(*) FROM limites_acceso WHERE clave=:c', c=llave)
                self.assertEqual(cur.fetchone()[0], 0)
