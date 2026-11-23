"""Acceso académico con cuentas sintéticas propias; sin cámara ni personas reales."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import os
import unittest
from unittest.mock import patch
from uuid import uuid4


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE')=='1','Requiere Oracle 010.')
class PruebaAcademicaOracleTest(unittest.TestCase):
    def setUp(self):
        import oracledb
        from src.base_datos.configuracion import obtener_conexion
        from src.servicios import clave_maestra_pruebas as claves, verificacion_identidad as identidad, sesiones_servidor as sesiones
        self.claves,self.identidad,self.sesiones=claves,identidad,sesiones
        self.conn=obtener_conexion();self.alumnos=[];self.addCleanup(self.limpiar)
        self.maestra='ClaveSinteticaAcademicaOracle!2026'
        self.cfg={'ESTUDIANTE_CLAVE_MAESTRA':self.maestra,
            'ESTUDIANTE_CLAVE_MAESTRA_HASTA':(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat()}
        p=patch.object(claves,'obtener_configuracion',side_effect=lambda k,d=None:self.cfg.get(k,d));p.start();self.addCleanup(p.stop)
        p=patch.object(identidad,'_clave',return_value=b'p'*32);p.start();self.addCleanup(p.stop)
        with self.conn.cursor() as cur:
            for activo in (1,1,0):
                codigo=('DEMO_'+uuid4().hex[:18]).upper();salida=cur.var(oracledb.NUMBER)
                cur.execute("INSERT INTO estudiantes(nombre,codigo_institucional,activo) VALUES('Fixture academico',:c,:a) RETURNING estudiante_id INTO :i",
                            c=codigo,a=activo,i=salida)
                self.alumnos.append((int(salida.getvalue()[0]),codigo))
        self.conn.commit()

    def limpiar(self):
        self.conn.rollback()
        with self.conn.cursor() as cur:
            for i,codigo in self.alumnos:
                cur.execute("DELETE FROM eventos_gestion WHERE entidad='VERIFICACION' AND entidad_id=:i",i=i)
                cur.execute("DELETE FROM sesiones_usuario WHERE rol='ESTUDIANTE' AND actor_id=:i",i=i)
                cur.execute('DELETE FROM estudiantes WHERE estudiante_id=:i',i=i)
                cur.execute('DELETE FROM limites_acceso WHERE clave=:c',c=sha256(('prueba_academica:'+codigo).encode()).hexdigest())
        self.conn.commit();self.conn.close()

    def autenticar(self,n=0,clave=None):
        return self.identidad.autenticar_prueba_academica(self.alumnos[n][1],self.maestra if clave is None else clave)

    def abrir(self,perfil):
        return self.sesiones.abrir('estudiante',perfil['estudiante_id'],prueba_identidad=perfil['_prueba_identidad'])

    def test_misma_clave_abre_dos_alumnos_sin_excepcion_y_registra_metodo_real(self):
        for n in (0,1):
            perfil=self.autenticar(n);token=self.abrir(perfil)
            self.sesiones.validar('estudiante',self.alumnos[n][0],token)
            with self.conn.cursor() as cur:
                cur.execute('SELECT estado_verificacion,factores_verificados,excepcion_activa,clave_hash,autorizado_por,autorizado_docente_por FROM verificacion_estudiantes WHERE estudiante_id=:i',i=self.alumnos[n][0])
                self.assertEqual(cur.fetchone(),('PRUEBA_ACADEMICA',0,0,None,None,None))
                cur.execute('SELECT COUNT(*) FROM registros_asistencia WHERE estudiante_id=:i',i=self.alumnos[n][0]);self.assertEqual(cur.fetchone()[0],0)
                cur.execute("SELECT motivo FROM eventos_gestion WHERE entidad='VERIFICACION' AND entidad_id=:i AND accion='ACCESO_VERIFICADO'",i=self.alumnos[n][0])
                motivos=str(cur.fetchall());self.assertIn('PRUEBA_ACADEMICA',motivos);self.assertNotIn(self.maestra,motivos)

    def test_cuenta_inactiva_no_accede_ni_se_reactiva(self):
        self.assertIsNone(self.autenticar(2))
        with self.conn.cursor() as cur:
            cur.execute('SELECT activo FROM estudiantes WHERE estudiante_id=:i',i=self.alumnos[2][0]);self.assertEqual(cur.fetchone()[0],0)

    def test_cuenta_activa_sin_codigo_institucional_accede_por_id(self):
        import oracledb
        with self.conn.cursor() as cur:
            salida=cur.var(oracledb.NUMBER)
            cur.execute("INSERT INTO estudiantes(nombre) VALUES('Fixture sin codigo') RETURNING estudiante_id INTO :i",i=salida)
            i=int(salida.getvalue()[0]);self.alumnos.append((i,'ID:'+str(i)))
        self.conn.commit()
        perfil=self.identidad.autenticar_prueba_academica(str(i),self.maestra,por_id=True)
        token=self.abrir(perfil)
        self.sesiones.validar('estudiante',i,token)

    def test_fallos_bloquean_tambien_la_clave_correcta(self):
        for _ in range(5):self.assertIsNone(self.autenticar(clave='incorrecta'))
        self.assertIsNone(self.autenticar())

    def test_replay_o_cambio_de_cuenta_no_reemplaza_sesion_valida(self):
        perfil=self.autenticar();token=self.abrir(perfil)
        with self.assertRaises(PermissionError):self.abrir(perfil)
        with self.assertRaises(PermissionError):
            self.sesiones.abrir('estudiante',self.alumnos[1][0],prueba_identidad=perfil['_prueba_identidad'])
        self.sesiones.validar('estudiante',self.alumnos[0][0],token)

    def test_retirar_clave_corta_ambas_rutas_de_validacion_y_permite_cerrar(self):
        token=self.abrir(self.autenticar());self.cfg.clear()
        with self.assertRaises(self.sesiones.SesionInvalida):self.sesiones.validar('estudiante',self.alumnos[0][0],token)
        with self.assertRaises(self.sesiones.SesionInvalida):
            self.sesiones.validar_en_conexion(self.conn,'estudiante',self.alumnos[0][0],token)
        self.sesiones.cerrar('estudiante',self.alumnos[0][0],token)

    def test_biometria_posterior_usa_sesion_normal_y_estado_biometrico(self):
        self.abrir(self.autenticar())
        with self.conn.cursor() as cur:
            cur.execute('UPDATE estudiantes SET embedding_facial=:f WHERE estudiante_id=:i',f='['+','.join(['0.1']*128)+']',i=self.alumnos[0][0])
        self.conn.commit()
        perfil=self.identidad.acreditar_biometria({'estudiante_id':self.alumnos[0][0],'nombre':'Fixture'})
        token=self.abrir(perfil);self.cfg.clear()
        self.sesiones.validar('estudiante',self.alumnos[0][0],token)
        with self.conn.cursor() as cur:
            cur.execute('SELECT estado_verificacion FROM verificacion_estudiantes WHERE estudiante_id=:i',i=self.alumnos[0][0])
            self.assertEqual(cur.fetchone()[0],'BIOMETRICA_COMPLETA')
