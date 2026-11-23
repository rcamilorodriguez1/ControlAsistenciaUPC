"""Cuentas sintéticas propias y limpieza por ID. Nunca modifica una cuenta existente."""
import json
import os
import secrets
import unittest
from hashlib import sha256
from uuid import uuid4
from unittest.mock import patch


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE') == '1', 'Requiere Oracle 008.')
class ExcepcionesOracleTest(unittest.TestCase):
    def setUp(self):
        import oracledb
        from src.base_datos.configuracion import obtener_conexion
        from src.servicios import verificacion_identidad as identidad
        from src.servicios import excepciones_biometricas as gestion
        from src.servicios import sesiones_servidor as sesiones
        self.oracle = oracledb
        self.identidad, self.gestion, self.sesiones = identidad, gestion, sesiones
        self.conn = obtener_conexion()
        self.estudiantes = []
        self.admin = None
        self.huellas = []
        self.addCleanup(self.limpiar)
        parche = patch.object(identidad, '_clave', return_value=b's' * 32)
        parche.start(); self.addCleanup(parche.stop)
        self.codigo = 'EXC_' + uuid4().hex[:18]
        self.documento = str(secrets.randbelow(900000000) + 100000000)
        self.clave = 'PruebaLocalSinIdentidad!2026'
        self.huellas.append(identidad.huella_documento('CC', self.documento)[0])
        with self.conn.cursor() as cur:
            def insertar(sql, **kw):
                out = cur.var(oracledb.NUMBER)
                cur.execute(sql + ' RETURNING ' + kw.pop('columna') + ' INTO :s', s=out, **kw)
                return int(out.getvalue()[0])
            self.admin = insertar("INSERT INTO administradores(usuario,nombre,contrasena) VALUES(:u,'Fixture excepciones','FIXTURE')",
                                  columna='administrador_id', u=self.codigo)
            self.estudiante = insertar("INSERT INTO estudiantes(nombre,codigo_institucional) VALUES(:u,:u)",
                                       columna='estudiante_id', u=self.codigo)
            self.estudiantes.append(self.estudiante)
            self.token_admin = secrets.token_urlsafe(32)
            cur.callproc('pkg_sesiones.abrir', ['ADMINISTRADOR', self.admin, sha256(self.token_admin.encode()).hexdigest()])
        self.conn.commit()
        # Usa el pool administrativo real y sus permisos limitados, con una sesión sintética real.
        parche = patch('src.base_datos.administracion._actor', return_value=('administrador', self.admin, self.token_admin))
        parche.start(); self.addCleanup(parche.stop)

    def limpiar(self):
        self.conn.rollback()
        try:
            with self.conn.cursor() as cur:
                cur.callproc('pkg_auditoria.limpiar_contexto')
                for i in self.estudiantes:
                    cur.execute("DELETE FROM eventos_gestion WHERE entidad='VERIFICACION' AND entidad_id=:i", i=i)
                    cur.execute("DELETE FROM sesiones_usuario WHERE rol='ESTUDIANTE' AND actor_id=:i", i=i)
                    cur.execute('DELETE FROM estudiantes WHERE estudiante_id=:i', i=i)
                for huella in self.huellas:
                    cur.execute('DELETE FROM limites_acceso WHERE clave=:c', c=sha256(('excepcion:' + huella).encode()).hexdigest())
                if self.admin:
                    cur.execute("DELETE FROM eventos_gestion WHERE actor_rol='ADMINISTRADOR' AND actor_id=:i", i=self.admin)
                    cur.execute("DELETE FROM sesiones_usuario WHERE rol='ADMINISTRADOR' AND actor_id=:i", i=self.admin)
                    cur.execute('DELETE FROM administradores WHERE administrador_id=:i', i=self.admin)
            self.conn.commit()
        finally:
            self.conn.close()

    def estado(self):
        return next(f for f in self.gestion.listar(self.codigo) if f['estudiante_id'] == self.estudiante)

    def autorizar(self, **cambios):
        valores = dict(estudiante_id=self.estudiante, tipo='CC', documento=self.documento, contrasena=self.clave,
            categoria='TECNICA', referencia='EXP-SINTETICO', dias=30, version=int(self.estado()['version_credencial']), documento_comprobado=True)
        valores.update(cambios)
        i = self.gestion.autorizar(**valores)
        if i not in self.estudiantes:
            self.estudiantes.append(i)
        return i

    def autenticar(self, clave=None):
        return self.identidad.autenticar_excepcion('CC', self.documento, self.clave if clave is None else clave)

    def abrir(self, perfil):
        return self.sesiones.abrir('estudiante', perfil['estudiante_id'], prueba_identidad=perfil['_prueba_identidad'])

    def test_sin_biometricos_accede_y_queda_excepcional_con_auditoria(self):
        self.autorizar()
        self.assertEqual(self.estado()['estado_verificacion'], 'PENDIENTE')
        perfil = self.autenticar()
        token = self.abrir(perfil)
        self.sesiones.validar('estudiante', self.estudiante, token)
        estado = self.estado()
        self.assertEqual((estado['estado_verificacion'], estado['factores_verificados'], estado['tiene_rostro']), ('EXCEPCIONAL', 0, 0))
        self.assertEqual(estado['documento'], '****' + self.documento[-4:])
        self.assertNotIn('clave_hash', estado)
        self.assertNotIn('documento_huella', estado)
        with self.conn.cursor() as cur:
            cur.execute("SELECT accion,motivo FROM eventos_gestion WHERE entidad='VERIFICACION' AND entidad_id=:i", i=self.estudiante)
            eventos = cur.fetchall()
            self.assertTrue({'EXCEPCION_AUTORIZADA', 'CREDENCIAL_VALIDADA', 'ACCESO_VERIFICADO'}.issubset({e[0] for e in eventos}))
            self.assertNotIn(self.documento, str(eventos))
            self.assertNotIn(self.clave, str(eventos))

    def test_renovacion_de_clave_invalida_pruebas_y_sesiones_previas(self):
        self.autorizar()
        token = self.abrir(self.autenticar())
        prueba_anterior = self.autenticar()
        nueva = 'OtraClaveSinteticaPrivada!2026'
        self.autorizar(contrasena=nueva)
        with self.assertRaises(self.sesiones.SesionInvalida):
            self.sesiones.validar('estudiante', self.estudiante, token)
        with self.assertRaises(PermissionError):
            self.abrir(prueba_anterior)
        self.assertIsNone(self.autenticar())
        perfil = self.autenticar(nueva)
        self.sesiones.validar('estudiante', self.estudiante, self.abrir(perfil))

    def test_cuenta_inactiva_no_accede_ni_se_reactiva_mediante_excepcion(self):
        self.autorizar()
        token = self.abrir(self.autenticar())
        with self.conn.cursor() as cur:
            cur.execute('UPDATE estudiantes SET activo=0 WHERE estudiante_id=:i', i=self.estudiante)
        self.conn.commit()
        self.assertIsNone(self.autenticar())
        with self.assertRaises(self.sesiones.SesionInvalida):
            self.sesiones.validar('estudiante', self.estudiante, token)
        with self.assertRaises(ValueError):
            self.autorizar()
        self.assertEqual(self.estado()['activo'], 0)

    def test_error_de_clave_limita_intentos_y_registra_fallos(self):
        self.autorizar()
        for _ in range(5):
            self.assertIsNone(self.autenticar('incorrecta'))
        self.assertIsNone(self.autenticar())
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM eventos_gestion WHERE entidad='VERIFICACION' AND entidad_id=:i AND accion='VALIDACION_FALLIDA'", i=self.estudiante)
            self.assertEqual(cur.fetchone()[0], 6)
        self.assertEqual(self.estado()['estado_verificacion'], 'PENDIENTE')

    def test_revocacion_invalida_token_y_prueba_emitida_previamente(self):
        self.autorizar()
        token = self.abrir(self.autenticar())
        prueba_anterior = self.autenticar()
        self.gestion.revocar(self.estudiante, 'Fin de autorización sintética', version=int(self.estado()['version_credencial']))
        with self.assertRaises(self.sesiones.SesionInvalida):
            self.sesiones.validar('estudiante', self.estudiante, token)
        with self.assertRaises(PermissionError):
            self.abrir(prueba_anterior)
        self.assertIsNone(self.autenticar())
        self.assertEqual(self.estado()['estado_verificacion'], 'EXCEPCIONAL')  # Conserva el último resultado, no lo falsea.

    def test_vencimiento_impide_nuevos_accesos_y_corta_sesion_existente(self):
        self.autorizar()
        token = self.abrir(self.autenticar())
        with self.conn.cursor() as cur:
            cur.execute("UPDATE verificacion_estudiantes SET expira_en=SYSTIMESTAMP-INTERVAL '1' SECOND WHERE estudiante_id=:i", i=self.estudiante)
        self.conn.commit()
        self.assertIsNone(self.autenticar())
        with self.assertRaises(self.sesiones.SesionInvalida):
            self.sesiones.validar('estudiante', self.estudiante, token)

    def test_prueba_de_un_solo_uso_y_apertura_sin_prueba_no_reemplazan_token(self):
        self.autorizar()
        perfil = self.autenticar()
        token = self.abrir(perfil)
        for prueba in (perfil['_prueba_identidad'], None):
            with self.assertRaises(PermissionError):
                self.sesiones.abrir('estudiante', self.estudiante, prueba_identidad=prueba)
            self.sesiones.validar('estudiante', self.estudiante, token)

    def test_documento_unico_y_version_obsoleta_no_modifican_cuenta(self):
        self.autorizar()
        with self.assertRaises(ValueError):
            self.autorizar(estudiante_id=None, nombre='Duplicado sintético', codigo_institucional=self.codigo + '2', version=0)
        with self.assertRaises(ValueError):
            self.autorizar(version=0)
        self.assertEqual(self.estado()['excepcion_vigente'], 1)

    def test_alta_administrativa_sin_rostro_ni_voz(self):
        nuevo = self.autorizar(estudiante_id=None, nombre='Alta sintética sin muestras', codigo_institucional=self.codigo + '2', version=0)
        perfil = self.autenticar()
        self.assertEqual(perfil['estudiante_id'], nuevo)
        self.sesiones.validar('estudiante', nuevo, self.abrir(perfil))

    def test_biometria_tras_excepcion_registra_el_metodo_real_sin_contar_la_voz(self):
        self.autorizar()
        self.abrir(self.autenticar())
        with self.conn.cursor() as cur:
            cur.execute('UPDATE estudiantes SET embedding_facial=:f WHERE estudiante_id=:i', f=json.dumps([.1] * 128), i=self.estudiante)
        self.conn.commit()
        perfil = self.identidad.acreditar_biometria({'estudiante_id': self.estudiante, 'nombre': 'Fixture'})
        self.abrir(perfil)
        estado = self.estado()
        self.assertEqual((estado['estado_verificacion'], estado['factores_verificados'], estado['factores_requeridos']), ('BIOMETRICA_COMPLETA', 1, 1))
        self.assertEqual(estado['excepcion_activa'], 1)

    def test_paquete_rechaza_contexto_estudiantil_y_pool_sin_dml(self):
        from src.base_datos import administracion
        with self.conn.cursor() as cur:
            cur.callproc('pkg_auditoria.establecer_contexto', ['ESTUDIANTE', self.estudiante, None])
            with self.conn.cursor() as salida, self.assertRaises(self.oracle.DatabaseError) as exc:
                cur.callproc('pkg_excepciones.listar', [None, salida])
            self.assertEqual(exc.exception.args[0].code, 20101)
            cur.callproc('pkg_auditoria.limpiar_contexto')
        with administracion.obtener_pool_admin().acquire() as conn, conn.cursor() as cur:
            with self.assertRaises(self.oracle.DatabaseError) as exc:
                cur.execute('UPDATE ' + administracion.propietario() + '.verificacion_estudiantes SET excepcion_activa=1')
            self.assertIn(exc.exception.args[0].code, (942, 1031))  # Oracle también oculta el objeto sin permisos.
