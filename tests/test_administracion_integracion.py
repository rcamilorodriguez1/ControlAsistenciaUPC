import json
import os
import unittest
from unittest.mock import patch
from uuid import uuid4
import test_disparadores_integracion as fixtures


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE') == '1', 'Requiere Oracle 006.')
class AdministracionIntegracionTest(unittest.TestCase):
    limpiar = fixtures.DisparadoresIntegracionTest.limpiar
    contar_tablas = fixtures.DisparadoresIntegracionTest.contar_tablas
    establecer = fixtures.DisparadoresIntegracionTest.establecer
    preparar_asistencia = fixtures.DisparadoresIntegracionTest.preparar_asistencia
    esperar_error = fixtures.DisparadoresIntegracionTest.esperar_error

    def setUp(self):
        fixtures.DisparadoresIntegracionTest.setUp(self)
        with self.conn.cursor() as cur:
            salida = cur.var(self.oracledb.NUMBER)
            self.usuario_admin = 'test_admin_' + uuid4().hex[:16]
            cur.execute("INSERT INTO administradores(usuario,nombre,contrasena) VALUES(:u,'Administrador de prueba','FIXTURE') RETURNING administrador_id INTO :s", u=self.usuario_admin, s=salida)
            self.admin = int(salida.getvalue()[0])
        self.establecer('ADMINISTRADOR', self.admin)

    def version(self, tabla, columna, identidad):
        with self.conn.cursor() as cur:
            cur.execute('SELECT TO_CHAR(version_edicion,\'TM9\') FROM '+tabla+' WHERE '+columna+'=:i', i=identidad)
            return cur.fetchone()[0]

    def test_lectura_exige_admin_y_no_entrega_hashes_ni_biometria(self):
        with self.conn.cursor() as cur, self.conn.cursor() as salida:
            cur.callproc('pkg_administracion.cuentas', ['PROFESOR', None, salida])
            self.assertNotIn('CONTRASENA', [c[0] for c in salida.description])
            cur.callproc('pkg_administracion.cuentas', ['ESTUDIANTE', None, salida])
            self.assertFalse({'EMBEDDING_FACIAL','EMBEDDING_VOZ'} & {c[0] for c in salida.description})
            self.establecer()
            with self.assertRaises(self.oracledb.DatabaseError) as error:
                cur.callproc('pkg_administracion.cuentas', ['PROFESOR', None, salida])
            self.assertEqual(error.exception.args[0].code, 20101)

    def test_cuenta_desactivada_pierde_permisos_incluso_con_contexto_anterior(self):
        with self.conn.cursor() as cur, self.conn.cursor() as salida:
            cur.execute('UPDATE administradores SET activo=0 WHERE administrador_id=:a', a=self.admin)
            with self.assertRaises(self.oracledb.DatabaseError) as error:
                cur.callproc('pkg_administracion.listar_materias', [None, salida])
            self.assertEqual(error.exception.args[0].code, 20101)

    def test_editar_materia_audita_y_rechaza_version_obsoleta(self):
        anterior = self.version('materias', 'materia_id', self.materia)
        codigo = 'ADM-' + uuid4().hex[:16]
        with self.conn.cursor() as cur:
            args = [self.materia, codigo, 'Materia revisada', 'Ñ-01', self.profesor, 1, 'Corrección de catálogo', anterior]
            cur.callproc('pkg_administracion.editar_materia', args)
            cur.execute("SELECT actor_rol,actor_id,valores_anteriores,valores_nuevos FROM eventos_gestion WHERE entidad='MATERIA' AND entidad_id=:i", i=self.materia)
            rol, actor, antes, despues = cur.fetchone()
            self.assertEqual((rol, actor), ('ADMINISTRADOR', self.admin))
            if hasattr(antes, 'read'): antes = antes.read()
            if hasattr(despues, 'read'): despues = despues.read()
            antes = json.loads(antes) if isinstance(antes, str) else antes
            despues = json.loads(despues) if isinstance(despues, str) else despues
            self.assertEqual(despues['nombre'], 'Materia revisada')
            self.assertNotEqual(antes['nombre'], despues['nombre'])
            with self.assertRaises(self.oracledb.DatabaseError) as error: cur.callproc('pkg_administracion.editar_materia', args)
            self.assertEqual(error.exception.args[0].code, 20106)

    def test_archivar_estudiante_conserva_asistencia_y_registra_retiro_con_admin(self):
        self.establecer(); asistencia = self.preparar_asistencia(); self.establecer('ADMINISTRADOR', self.admin)
        with self.conn.cursor() as cur:
            cur.execute("UPDATE estudiantes SET embedding_facial='[0.1]',embedding_voz='[0.2]' WHERE estudiante_id=:e", e=self.estudiante)
            version = self.version('estudiantes','estudiante_id',self.estudiante)
            cur.callproc('pkg_administracion.editar_estudiante', [self.estudiante, None, 'Estudiante revisado', 0, 'Retiro institucional', version])
            cur.execute('SELECT activo,embedding_facial,embedding_voz FROM estudiantes WHERE estudiante_id=:e', e=self.estudiante)
            self.assertEqual(cur.fetchone(), (0, None, None))
            cur.execute('SELECT COUNT(*) FROM registros_asistencia WHERE asistencia_id=:a', a=asistencia)
            self.assertEqual(cur.fetchone()[0], 1)
            cur.execute("SELECT actor_rol,actor_id,motivo FROM historial_matriculas WHERE estudiante_id=:e AND accion='RETIRO'", e=self.estudiante)
            self.assertEqual(cur.fetchone(), ('ADMINISTRADOR', self.admin, 'Retiro institucional'))

    def test_no_reasigna_docente_si_existen_clases(self):
        self.establecer(); self.preparar_asistencia(); self.establecer('ADMINISTRADOR', self.admin)
        version = self.version('materias','materia_id',self.materia)
        self.esperar_error(20103, 'pkg_administracion.editar_materia', [self.materia,'TRASPASO','Materia','A',self.otro_profesor,1,'Cambio de docente',version])

    def test_reset_de_clave_no_incluye_hash_en_la_auditoria(self):
        from src.base_datos.bd import cifrar_contrasena
        hashed = cifrar_contrasena('ClaveDePrueba!9382')
        version = self.version('profesores','profesor_id',self.profesor)
        with self.conn.cursor() as cur:
            usuario = 'edit_' + uuid4().hex[:16]
            cur.callproc('pkg_administracion.editar_profesor', [self.profesor,usuario,'Docente revisado',1,hashed,'Restablecer acceso',version])
            cur.execute("SELECT accion,valores_anteriores,valores_nuevos FROM eventos_gestion WHERE entidad='PROFESOR' AND entidad_id=:i", i=self.profesor)
            filas = str(cur.fetchall())
            self.assertIn('REINICIO_CLAVE', filas)
            self.assertNotIn(hashed, filas)
            self.assertNotIn('ClaveDePrueba', filas)

    def test_error_de_segundo_cambio_revierte_archivo_parcial(self):
        version = self.version('profesores','profesor_id',self.profesor)
        with self.conn.cursor() as cur:
            cur.execute('SELECT usuario FROM profesores WHERE profesor_id=:p', p=self.otro_profesor)
            duplicado = cur.fetchone()[0]
            with self.assertRaises(self.oracledb.IntegrityError):
                cur.callproc('pkg_administracion.editar_profesor', [self.profesor,duplicado,'Otro nombre',0,None,'Intento duplicado',version])
            cur.execute('SELECT activo FROM profesores WHERE profesor_id=:p', p=self.profesor)
            self.assertEqual(cur.fetchone()[0], 1)
            cur.execute('SELECT activo FROM materias WHERE materia_id=:m', m=self.materia)
            self.assertEqual(cur.fetchone()[0], 1)

    def test_archivo_docente_audita_tambien_las_materias_afectadas(self):
        version = self.version('profesores','profesor_id',self.profesor)
        with self.conn.cursor() as cur:
            cur.execute('SELECT usuario FROM profesores WHERE profesor_id=:p', p=self.profesor)
            usuario = cur.fetchone()[0]
            cur.callproc('pkg_administracion.editar_profesor', [self.profesor,usuario,'Docente archivado',0,None,'Finalizó vinculación',version])
            cur.execute("SELECT actor_rol,actor_id FROM eventos_gestion WHERE entidad='MATERIA' AND entidad_id=:m AND accion='ARCHIVO_DOCENTE'", m=self.materia)
            self.assertEqual(cur.fetchone(), ('ADMINISTRADOR', self.admin))

    def test_autenticacion_limita_intentos_y_no_retiene_hash_en_perfil(self):
        from src.base_datos import administracion, bd
        conexion = self.conn
        class SinCommit:
            def cursor(self): return conexion.cursor()
            def commit(self): pass
        with self.conn.cursor() as cur:
            cur.execute('UPDATE administradores SET contrasena=:c WHERE administrador_id=:a', c=bd.cifrar_contrasena('ClaveAdminPrueba!8271'), a=self.admin)
            with patch.object(bd, 'ejecutar_con_reintentos', side_effect=lambda op, **kw: op(SinCommit())):
                perfil = administracion.autenticar(self.usuario_admin, 'ClaveAdminPrueba!8271')
                self.assertEqual(perfil['administrador_id'], self.admin)
                self.assertNotIn('contrasena', perfil)
                for _ in range(5): self.assertIsNone(administracion.autenticar(self.usuario_admin, 'ErrorDePrueba'))
                self.assertIsNone(administracion.autenticar(self.usuario_admin, 'ClaveAdminPrueba!8271'))
