import os
from hashlib import sha256
import secrets
import unittest
from unittest.mock import patch
from uuid import uuid4
from src.servicios import excepciones_docentes as servicio


class ExcepcionesDocentesTest(unittest.TestCase):
    def test_otro_rol_no_adquiere_conexion_tecnica(self):
        for actor in (None, ('estudiante', 1, 't'), ('administrador', 1, 't')):
            with patch.object(servicio, 'obtener_actor', return_value=actor), \
                 patch.object(servicio.datos, 'obtener_pool_admin') as pool:
                with self.assertRaises(PermissionError): servicio.listar(1)
                pool.assert_not_called()

    def test_documento_clave_y_vigencia_se_validan_antes_de_escribir(self):
        base = dict(materia_id=1, estudiante_id=2, tipo='CC', documento='123456789',
            contrasena='ClaveDePruebaSolamente!', categoria='TECNICA', referencia='TEST', dias=1,
            version=0, documento_comprobado=True)
        with patch.object(servicio, '_actor', return_value=('profesor', 1, 't')), \
             patch.object(servicio, '_ejecutar') as escribir:
            for cambios in (dict(documento_comprobado=False), dict(contrasena='corta'), dict(dias=0),
                            dict(dias=True), dict(version=-1), dict(materia_id=True)):
                with self.subTest(cambios=cambios), self.assertRaises(ValueError):
                    servicio.autorizar(**(base | cambios))
            escribir.assert_not_called()


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE') == '1', 'Requiere Oracle 009 y cuentas técnicas locales.')
class ExcepcionesDocentesOracleTest(unittest.TestCase):
    def setUp(self):
        import oracledb
        from src.base_datos.configuracion import obtener_conexion
        from src.servicios import verificacion_identidad, sesiones_servidor
        import test_excepciones_oracle as soporte
        self.oracle = oracledb
        self.identidad, self.sesiones = verificacion_identidad, sesiones_servidor
        self.fixture = soporte.ExcepcionesOracleTest('runTest')
        self.docentes, self.materias = [], []
        self.addCleanup(self.limpiar_docentes)
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.conn = self.fixture.conn
        self.codigo = 'DOCEX_' + uuid4().hex[:12]
        self.tokens = []
        with self.conn.cursor() as cur:
            for indice in range(2):
                out = cur.var(oracledb.NUMBER)
                cur.execute("INSERT INTO profesores(usuario,nombre,contrasena) VALUES(:u,'Fixture docente excepcion','FIXTURE') RETURNING profesor_id INTO :s",
                    u=self.codigo+str(indice), s=out)
                pid = int(out.getvalue()[0]); self.docentes.append(pid)
                cur.execute("INSERT INTO materias(codigo_materia,nombre,seccion,profesor_id) VALUES(:u,'Fixture materia excepcion','A',:p) RETURNING materia_id INTO :s",
                    u=self.codigo+str(indice), p=pid, s=out)
                mid = int(out.getvalue()[0]); self.materias.append(mid)
                cur.callproc('pkg_auditoria.establecer_contexto', ['PROFESOR', pid, None])
                cur.callproc('pkg_asistencia.matricular_estudiante', [self.fixture.estudiante, mid])
                token = secrets.token_urlsafe(32); self.tokens.append(token)
                cur.callproc('pkg_sesiones.abrir', ['PROFESOR', pid, sha256(token.encode()).hexdigest()])
            cur.callproc('pkg_auditoria.limpiar_contexto')
        self.conn.commit()
        self.actor = ('profesor', self.docentes[0], self.tokens[0])
        p = patch.object(servicio, 'obtener_actor', side_effect=lambda **kw: self.actor)
        p.start(); self.addCleanup(p.stop)

    def limpiar_docentes(self):
        from src.base_datos.configuracion import obtener_conexion
        with obtener_conexion() as conn, conn.cursor() as cur:
            for mid in self.materias:
                cur.execute('DELETE FROM historial_matriculas WHERE materia_id=:i', i=mid)
                cur.execute('DELETE FROM materias WHERE materia_id=:i', i=mid)
            for pid in self.docentes:
                cur.execute("DELETE FROM eventos_gestion WHERE actor_rol='PROFESOR' AND actor_id=:i", i=pid)
                cur.execute("DELETE FROM sesiones_usuario WHERE rol='PROFESOR' AND actor_id=:i", i=pid)
                cur.execute('DELETE FROM profesores WHERE profesor_id=:i', i=pid)
            conn.commit()

    def autorizar(self, mid=None, version=0, **cambios):
        valores = dict(materia_id=mid or self.materias[0], estudiante_id=self.fixture.estudiante,
            tipo='CC', documento=self.fixture.documento, contrasena=self.fixture.clave,
            categoria='TECNICA', referencia='SOL-SINTETICA', dias=1, version=version, documento_comprobado=True)
        return servicio.autorizar(**(valores | cambios))

    def test_entrega_manual_permite_acceso_y_revocacion_corta_la_sesion(self):
        self.autorizar()
        alumno = servicio.listar(self.materias[0])[0]
        self.assertEqual((alumno['excepcion_vigente'], alumno['puede_revocar']), (1, 1))
        perfil = self.fixture.autenticar()
        token = self.fixture.abrir(perfil)
        self.sesiones.validar('estudiante', self.fixture.estudiante, token)
        version = int(servicio.listar(self.materias[0])[0]['version_credencial'])
        servicio.revocar(self.materias[0], self.fixture.estudiante, 'Fin de prueba', version=version)
        with self.assertRaises(self.sesiones.SesionInvalida):
            self.sesiones.validar('estudiante', self.fixture.estudiante, token)
        self.assertIsNone(self.fixture.autenticar())
        with self.conn.cursor() as cur:
            cur.execute("SELECT actor_rol,actor_id FROM eventos_gestion WHERE entidad='VERIFICACION' AND entidad_id=:i AND accion='EXCEPCION_AUTORIZADA'", i=self.fixture.estudiante)
            self.assertEqual(cur.fetchall(), [('PROFESOR', self.docentes[0])])

    def test_otra_materia_y_otro_autorizador_se_rechazan(self):
        with self.assertRaises(PermissionError): servicio.listar(self.materias[1])
        self.autorizar()
        self.actor = ('profesor', self.docentes[1], self.tokens[1])
        self.assertEqual(servicio.listar(self.materias[1])[0]['puede_autorizar'], 0)
        with self.assertRaises(PermissionError): self.autorizar(self.materias[1], version=1)
        with self.assertRaises(PermissionError): servicio.revocar(self.materias[1], self.fixture.estudiante, 'Ajena', version=1)

    def test_matricula_version_y_sesion_se_comprueban_en_servidor(self):
        self.autorizar()
        with self.assertRaises(ValueError): self.autorizar(version=0)
        with self.conn.cursor() as cur:
            cur.callproc('pkg_auditoria.establecer_contexto', ['PROFESOR', self.docentes[0], None])
            cur.callproc('pkg_asistencia.retirar_estudiante', [self.fixture.estudiante, self.materias[0], 'Fin de prueba'])
        self.conn.commit()
        with self.assertRaises(PermissionError): self.autorizar(version=1)
        self.actor = ('profesor', self.docentes[0], 'token-revocado-de-prueba')
        with self.assertRaises(self.sesiones.SesionInvalida): servicio.listar(self.materias[0])

    def test_administracion_puede_reemplazar_y_docente_no_puede_sobrescribir(self):
        self.autorizar()
        self.fixture.autorizar()
        self.assertEqual(servicio.listar(self.materias[0])[0]['puede_autorizar'], 0)
        with self.assertRaises(PermissionError): self.autorizar(version=2)

    def test_credencial_vencida_no_inicia_sesion(self):
        self.autorizar()
        with self.conn.cursor() as cur:
            cur.execute("UPDATE verificacion_estudiantes SET expira_en=SYSTIMESTAMP-INTERVAL '1' SECOND WHERE estudiante_id=:i", i=self.fixture.estudiante)
        self.conn.commit()
        self.assertEqual(servicio.listar(self.materias[0])[0]['excepcion_vigente'], 0)
        self.assertIsNone(self.fixture.autenticar())
