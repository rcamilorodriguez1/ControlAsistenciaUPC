"""Sesiones reales en Oracle: revocacion, caducidad y concurrencia; cuentas propias desechables."""
import os
import secrets
import unittest
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from threading import Barrier,Event
from uuid import uuid4


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE')=='1','Requiere Oracle 007.')
class SesionesServidorIntegracionTest(unittest.TestCase):
    def setUp(self):
        import oracledb
        from src.base_datos.configuracion import obtener_conexion
        self.oracle=oracledb;self.conectar=obtener_conexion;self.conn=obtener_conexion()
        self.ids={};self.addCleanup(self.limpiar)
        with self.conn.cursor() as cur:
            for rol,tabla,columna in [('PROFESOR','profesores','profesor_id'),('ESTUDIANTE','estudiantes','estudiante_id'),('ADMINISTRADOR','administradores','administrador_id')]:
                salida=cur.var(oracledb.NUMBER);u='SES_'+uuid4().hex[:18]
                if rol=='ESTUDIANTE': sql='INSERT INTO estudiantes(nombre,codigo_institucional) VALUES(\'Fixture sesion\',:u)'
                else: sql='INSERT INTO '+tabla+'(usuario,nombre,contrasena) VALUES(:u,\'Fixture sesion\',\'FIXTURE\')'
                cur.execute(sql+' RETURNING '+columna+' INTO :s',u=u,s=salida)
                self.ids[rol]=(int(salida.getvalue()[0]),tabla,columna)
        self.conn.commit()

    def limpiar(self):
        self.conn.rollback()
        with self.conn.cursor() as cur:
            for rol,(i,tabla,columna) in self.ids.items():
                cur.execute('DELETE FROM sesiones_usuario WHERE rol=:r AND actor_id=:i',r=rol,i=i)
                cur.execute('DELETE FROM '+tabla+' WHERE '+columna+'=:i',i=i)
        self.conn.commit();self.conn.close()

    def abrir(self,rol,conn=None):
        token=secrets.token_urlsafe(32);c=conn or self.conn
        with c.cursor() as cur:cur.callproc('pkg_sesiones.abrir',[rol,self.ids[rol][0],sha256(token.encode()).hexdigest()])
        c.commit();return token

    def validar(self,rol,token,conn=None):
        with (conn or self.conn).cursor() as cur:
            cur.callproc('pkg_sesiones.validar',[rol,self.ids[rol][0],sha256(token.encode()).hexdigest(),0])

    def error(self,rol,token,codigo):
        try:
            with self.assertRaises(self.oracle.DatabaseError) as e:self.validar(rol,token)
            self.assertEqual(e.exception.args[0].code,codigo)
        finally:self.conn.rollback()

    def test_sustitucion_y_cierre_para_los_tres_roles(self):
        for rol in self.ids:
            with self.subTest(rol=rol):
                primero=self.abrir(rol);segundo=self.abrir(rol)
                self.error(rol,primero,20201);self.validar(rol,segundo);self.conn.rollback()
                with self.conn.cursor() as cur:
                    cur.callproc('pkg_sesiones.cerrar',[rol,self.ids[rol][0],sha256(primero.encode()).hexdigest()])
                self.conn.commit();self.validar(rol,segundo);self.conn.rollback()
                with self.conn.cursor() as cur:cur.callproc('pkg_sesiones.cerrar',[rol,self.ids[rol][0],sha256(segundo.encode()).hexdigest()])
                self.conn.commit();self.error(rol,segundo,20202)

    def test_caducidad_por_inactividad_y_duracion_absoluta(self):
        for rol in self.ids:
            token=self.abrir(rol)
            with self.conn.cursor() as cur:cur.execute("UPDATE sesiones_usuario SET creada_en=SYSTIMESTAMP-INTERVAL '1' HOUR,actividad_en=SYSTIMESTAMP-INTERVAL '31' MINUTE WHERE rol=:r AND actor_id=:i",r=rol,i=self.ids[rol][0])
            self.conn.commit();self.error(rol,token,20203)
            token=self.abrir(rol)
            with self.conn.cursor() as cur:cur.execute("UPDATE sesiones_usuario SET creada_en=SYSTIMESTAMP-INTERVAL '9' HOUR,expira_en=SYSTIMESTAMP-INTERVAL '1' SECOND WHERE rol=:r AND actor_id=:i",r=rol,i=self.ids[rol][0])
            self.conn.commit();self.error(rol,token,20203)

    def test_desactivar_cuenta_revoca_su_autorizacion(self):
        for rol,(i,tabla,columna) in self.ids.items():
            token=self.abrir(rol)
            with self.conn.cursor() as cur:cur.execute('UPDATE '+tabla+' SET activo=0 WHERE '+columna+'=:i',i=i)
            self.conn.commit();self.error(rol,token,20204)

    def test_se_guarda_solo_hash_y_no_se_cruzan_roles(self):
        token=self.abrir('PROFESOR')
        with self.conn.cursor() as cur:
            cur.execute("SELECT token_hash FROM sesiones_usuario WHERE rol='PROFESOR' AND actor_id=:i",i=self.ids['PROFESOR'][0])
            self.assertEqual(cur.fetchone()[0],sha256(token.encode()).hexdigest())
        self.error('ESTUDIANTE',token,20205)

    def test_dos_inicios_simultaneos_dejan_un_solo_token_valido(self):
        for rol in self.ids:
            barrera=Barrier(2)
            def iniciar():
                with self.conectar() as c:
                    barrera.wait(timeout=10);return self.abrir(rol,c)
            with ThreadPoolExecutor(max_workers=2) as h:
                tareas=[h.submit(iniciar) for _ in range(2)]
                tokens=[t.result(timeout=15) for t in tareas]
            validos=0
            for token in tokens:
                try:self.validar(rol,token);validos+=1
                except self.oracle.DatabaseError as e:self.assertEqual(e.args[0].code,20201)
                finally:self.conn.rollback()
            self.assertEqual(validos,1)

    def test_reemplazo_espera_al_fin_de_la_operacion_protegida(self):
        token=self.abrir('PROFESOR');self.validar('PROFESOR',token)
        iniciada=Event();terminada=Event()
        def reemplazar():
            with self.conectar() as c:
                iniciada.set();nuevo=self.abrir('PROFESOR',c);terminada.set();return nuevo
        with ThreadPoolExecutor(max_workers=1) as h:
            tarea=h.submit(reemplazar)
            try:
                self.assertTrue(iniciada.wait(2));self.assertFalse(terminada.wait(.2))
            finally:self.conn.rollback()
            nuevo=tarea.result(timeout=10)
        self.error('PROFESOR',token,20201);self.validar('PROFESOR',nuevo);self.conn.rollback()

    def test_password_cambiado_no_admite_una_verificacion_anterior_al_cambio(self):
        from src.servicios import sesiones_servidor as servicio
        from src.base_datos.bd import cifrar_contrasena
        anterior=cifrar_contrasena('ClaveAnteriorFixture!39')
        actual=cifrar_contrasena('ClaveActualFixture!82')
        token=self.abrir('PROFESOR')
        with self.conn.cursor() as cur:cur.execute('UPDATE profesores SET contrasena=:h WHERE profesor_id=:i',h=actual,i=self.ids['PROFESOR'][0])
        self.conn.commit()
        with self.assertRaises(servicio.SesionInvalida):servicio.abrir('profesor',self.ids['PROFESOR'][0],anterior)
        self.validar('PROFESOR',token);self.conn.rollback()
        nuevo=servicio.abrir('profesor',self.ids['PROFESOR'][0],actual)
        self.error('PROFESOR',token,20201);self.validar('PROFESOR',nuevo);self.conn.rollback()
