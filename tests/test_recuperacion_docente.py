import os
import unittest
from hashlib import sha256
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import test_disparadores_integracion as fixtures


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE')=='1','Requiere Oracle 007.')
class RecuperacionDocenteIntegracionTest(unittest.TestCase):
    limpiar=fixtures.DisparadoresIntegracionTest.limpiar
    contar_tablas=fixtures.DisparadoresIntegracionTest.contar_tablas

    def setUp(self):
        fixtures.DisparadoresIntegracionTest.setUp(self)
        from src.base_datos import bd
        from src.servicios.recuperacion_acceso import restablecer_profesor
        self.restablecer=restablecer_profesor
        self.clave='ClaveInicialFixture!39'
        self.nueva='ClaveRenovadaFixture!74'
        self.autorizacion='AutorizacionSintetica!4928'
        with self.conn.cursor() as cur:
            cur.execute('UPDATE profesores SET contrasena=:h WHERE profesor_id=:i',h=bd.cifrar_contrasena(self.clave),i=self.profesor)
            cur.execute('SELECT usuario FROM profesores WHERE profesor_id=:i',i=self.profesor);self.usuario=cur.fetchone()[0].lower()
        conexion=self.conn
        class SinCommit:
            def cursor(_):return conexion.cursor()
            def commit(_):pass
        for parche in [patch('src.servicios.cuentas.obtener_configuracion',return_value=self.autorizacion),
                        patch.object(bd,'ejecutar_con_reintentos',side_effect=lambda op,**kw:op(SinCommit()))]:
            parche.start();self.addCleanup(parche.stop)

    def hash_actual(self):
        with self.conn.cursor() as cur:
            cur.execute('SELECT contrasena FROM profesores WHERE profesor_id=:i',i=self.profesor)
            return cur.fetchone()[0]

    def test_cambia_hash_revoca_sesiones_y_audita_sin_secretos(self):
        from src.base_datos import bd
        with self.conn.cursor() as cur:
            cur.callproc('pkg_sesiones.abrir',['PROFESOR',self.profesor,sha256(b'token-sintetico').hexdigest()])
            cur.execute('INSERT INTO limites_acceso(clave,intentos) VALUES(:c,5)',c=sha256(self.usuario.encode()).hexdigest())
        self.assertTrue(self.restablecer(self.usuario,self.autorizacion,self.nueva,self.nueva))
        self.assertTrue(bd.verificar_contrasena(self.nueva,self.hash_actual()))
        self.assertFalse(bd.verificar_contrasena(self.clave,self.hash_actual()))
        with self.conn.cursor() as cur:
            cur.execute("SELECT revocada_en FROM sesiones_usuario WHERE rol='PROFESOR' AND actor_id=:i",i=self.profesor)
            self.assertIsNotNone(cur.fetchone()[0])
            cur.execute("SELECT actor_rol,motivo,valores_anteriores,valores_nuevos FROM eventos_gestion WHERE entidad_id=:i AND accion='RESTABLECIMIENTO_CLAVE'",i=self.profesor)
            fila=cur.fetchone();self.assertEqual(fila[0],'SISTEMA');self.assertEqual(fila[2:],(None,None))
            self.assertNotIn(self.nueva,repr(fila));self.assertNotIn(self.autorizacion,repr(fila))
            cur.execute('SELECT COUNT(*) FROM limites_acceso WHERE clave=:c',c=sha256(self.usuario.encode()).hexdigest())
            self.assertEqual(cur.fetchone()[0],0)

    def test_autorizacion_incorrecta_no_cambia_la_cuenta_ni_crea_sesion(self):
        anterior=self.hash_actual()
        self.assertFalse(self.restablecer(self.usuario,'incorrecta',self.nueva,self.nueva))
        self.assertEqual(self.hash_actual(),anterior)
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sesiones_usuario WHERE rol='PROFESOR' AND actor_id=:i",i=self.profesor)
            self.assertEqual(cur.fetchone()[0],0)

    def test_usuario_inexistente_o_archivado_no_se_recupera(self):
        self.assertFalse(self.restablecer('usuario.inexistente.fixture',self.autorizacion,self.nueva,self.nueva))
        with self.conn.cursor() as cur:cur.execute('UPDATE profesores SET activo=0 WHERE profesor_id=:i',i=self.profesor)
        self.assertFalse(self.restablecer(self.usuario,self.autorizacion,self.nueva,self.nueva))

    def test_cinco_fallos_bloquean_quince_minutos_y_el_exito_limpia_el_limite(self):
        llave=sha256(('recuperacion:profesor:'+self.usuario).encode()).hexdigest()
        for _ in range(5):self.assertFalse(self.restablecer(self.usuario,'incorrecta',self.nueva,self.nueva))
        self.assertFalse(self.restablecer(self.usuario,self.autorizacion,self.nueva,self.nueva))
        with self.conn.cursor() as cur:
            cur.execute('SELECT intentos,bloqueado_hasta FROM limites_acceso WHERE clave=:c',c=llave)
            f=cur.fetchone();self.assertEqual(f[0],5);self.assertIsNotNone(f[1])
            cur.execute("UPDATE limites_acceso SET ventana_en=SYSTIMESTAMP-INTERVAL '16' MINUTE,bloqueado_hasta=SYSTIMESTAMP-INTERVAL '1' MINUTE WHERE clave=:c",c=llave)
        self.assertTrue(self.restablecer(self.usuario,self.autorizacion,self.nueva,self.nueva))
        with self.conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM limites_acceso WHERE clave=:c',c=llave);self.assertEqual(cur.fetchone()[0],0)


class RecuperacionDocenteInterfazTest(unittest.TestCase):
    def setUp(self):
        self.at=AppTest.from_file('../principal.py',default_timeout=35).run()
        next(b for b in self.at.button if b.label=='Portal del Profesor').click().run()
        self.at.button(key='olvide_clave_docente').click().run()
        self.assertFalse(self.at.exception)

    def campos(self):
        for i,v in zip(self.at.text_input,['docente.fixture','AutorizacionSintetica!45','Faro!Bosque7Luna*Reloj26','Faro!Bosque7Luna*Reloj26']):i.input(v)

    def test_recupera_y_limpia_secretos_sin_iniciar_sesion(self):
        self.campos()
        with patch('src.componentes.recuperar_clave.restablecer_profesor',return_value=True) as recuperar:
            self.at.button(key='restablecer_clave_docente').click().run()
            recuperar.assert_called_once()
        self.assertFalse(self.at.exception)
        self.assertFalse(self.at.session_state['sesion_iniciada'])
        self.assertEqual(len(self.at.text_input),2)
        self.assertTrue(all(i.value=='' for i in self.at.text_input))
        self.assertTrue(any('Contraseña restablecida' in s.value for s in self.at.success))
        valores=self.at.session_state.to_dict().values()
        self.assertNotIn('AutorizacionSintetica!45',valores)
        self.assertNotIn('Faro!Bosque7Luna*Reloj26',valores)

    def test_datos_invalidos_muestran_error_generico_y_no_abren_sesion(self):
        self.campos()
        with patch('src.componentes.recuperar_clave.restablecer_profesor',return_value=False):
            self.at.button(key='restablecer_clave_docente').click().run()
        self.assertFalse(self.at.exception)
        self.assertFalse(self.at.session_state['sesion_iniciada'])
        self.assertTrue(any('datos no coinciden' in e.value for e in self.at.error))

    def test_confirmacion_distinta_no_toca_oracle_y_cancelar_limpia_campos(self):
        self.campos();self.at.text_input[3].input('DistintaClave!938')
        with patch('src.servicios.recuperacion_acceso.bd.ejecutar_con_reintentos') as ejecutar:
            self.at.button(key='restablecer_clave_docente').click().run();ejecutar.assert_not_called()
        self.assertTrue(any('no coincide' in w.value for w in self.at.warning))
        self.at.button(key='volver_recuperacion_docente').click().run()
        self.assertFalse(self.at.exception);self.assertTrue(all(i.value=='' for i in self.at.text_input))
