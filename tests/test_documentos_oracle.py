"""Documento como identificador; datos sintéticos propios y limpieza por IDs."""
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import json
import os
import secrets
import unittest
from unittest.mock import patch
from uuid import uuid4


@unittest.skipUnless(os.environ.get('UPC_TEST_ORACLE')=='1','Requiere Oracle 011.')
class DocumentosOracleTest(unittest.TestCase):
    def setUp(self):
        import oracledb
        from src.base_datos.configuracion import obtener_conexion
        from src.servicios import verificacion_identidad as identidad,clave_maestra_pruebas as claves,sesiones_servidor as sesiones
        self.oracle=oracledb;self.identidad=identidad;self.claves=claves;self.sesiones=sesiones
        self.conn=obtener_conexion();self.ids=[];self.docs=[];self.admin=None;self.addCleanup(self.limpiar)
        self.nombre='Fixture documento '+uuid4().hex[:12]
        self.clave='ClaveAcademicaSinteticaDocumentos!'
        self.cfg={'ESTUDIANTE_CLAVE_MAESTRA':self.clave,'ESTUDIANTE_CLAVE_MAESTRA_HASTA':(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat()}
        p=patch.object(claves,'obtener_configuracion',side_effect=lambda k,d=None:self.cfg.get(k,d));p.start();self.addCleanup(p.stop)
        p=patch.object(identidad,'_clave',return_value=b'q'*32);p.start();self.addCleanup(p.stop)

    def numero(self):
        valor=str(secrets.randbelow(9000000000000)+1000000000000);self.docs.append(valor);return valor

    def crear(self,documento=None,*,legado=False):
        documento=documento or self.numero();h,f=self.identidad.huella_documento('CC',documento)
        with self.conn.cursor() as cur:
            salida=cur.var(self.oracle.NUMBER)
            if legado:
                cur.execute('INSERT INTO estudiantes(nombre) VALUES(:n) RETURNING estudiante_id INTO :i',n=self.nombre,i=salida)
            else:
                cur.callproc('pkg_gestion.registrar_estudiante',[self.nombre,h,'CC',f,json.dumps([.1]*128),None,salida])
            valor=salida.getvalue();i=int(valor[0] if isinstance(valor,list) else valor);self.ids.append(i)
        self.conn.commit();return i,documento

    def contexto(self,i):
        with self.conn.cursor() as cur:cur.callproc('pkg_auditoria.establecer_contexto',['ESTUDIANTE',i,None])

    def editar(self,i,documento,version):
        h,f=self.identidad.huella_documento('CC',documento)
        with self.conn.cursor() as cur:cur.callproc('pkg_gestion.actualizar_documento',[i,h,'CC',f,version])

    def limpiar(self):
        self.conn.rollback()
        with self.conn.cursor() as cur:
            cur.callproc('pkg_auditoria.limpiar_contexto')
            for i in self.ids:
                cur.execute("DELETE FROM eventos_gestion WHERE entidad IN ('ESTUDIANTE','VERIFICACION') AND entidad_id=:i",i=i)
                cur.execute("DELETE FROM sesiones_usuario WHERE rol='ESTUDIANTE' AND actor_id=:i",i=i)
                cur.execute('DELETE FROM estudiantes WHERE estudiante_id=:i',i=i)
            for d in self.docs:
                h=self.identidad.huella_documento('CC',d)[0]
                for prefijo in ('prueba_academica:','excepcion:'):
                    cur.execute('DELETE FROM limites_acceso WHERE clave=:c',c=sha256((prefijo+h).encode()).hexdigest())
            if self.admin is not None:
                cur.execute("DELETE FROM sesiones_usuario WHERE rol='ADMINISTRADOR' AND actor_id=:i",i=self.admin)
                cur.execute('DELETE FROM administradores WHERE administrador_id=:i',i=self.admin)
        self.conn.commit();self.conn.close()

    def test_alta_documento_sin_codigo_y_acceso_maestro(self):
        i,d=self.crear()
        perfil=self.identidad.autenticar_prueba_academica('CC',d,self.clave)
        token=self.sesiones.abrir('estudiante',i,prueba_identidad=perfil['_prueba_identidad'])
        self.sesiones.validar('estudiante',i,token)
        with self.conn.cursor() as cur:
            cur.execute('SELECT e.codigo_institucional,v.documento_huella,v.documento_final,v.excepcion_activa FROM estudiantes e JOIN verificacion_estudiantes v ON v.estudiante_id=e.estudiante_id WHERE e.estudiante_id=:i',i=i)
            fila=cur.fetchone();self.assertIsNone(fila[0]);self.assertEqual(fila[1],self.identidad.huella_documento('CC',d)[0]);self.assertEqual(fila[2:],(d[-4:],0))
            cur.execute("SELECT motivo FROM eventos_gestion WHERE entidad IN ('ESTUDIANTE','VERIFICACION') AND entidad_id=:i",i=i)
            self.assertNotIn(d,str(cur.fetchall()))

    def test_documento_duplicado_revierte_toda_el_alta(self):
        _,d=self.crear()
        with self.conn.cursor() as cur:
            out=cur.var(self.oracle.NUMBER);h,f=self.identidad.huella_documento('CC',d)
            with self.assertRaises(self.oracle.IntegrityError):cur.callproc('pkg_gestion.registrar_estudiante',[self.nombre,h,'CC',f,json.dumps([.1]*128),None,out])
            cur.execute('SELECT COUNT(*) FROM estudiantes WHERE nombre=:n',n=self.nombre);self.assertEqual(cur.fetchone()[0],1)

    def test_driver_crea_documento_en_la_misma_transaccion_sin_codigo(self):
        from src.base_datos import bd
        d=self.numero()
        perfil=bd.crear_estudiante(self.nombre,[.1]*128,tipo_documento='CC',documento=d)[0]
        self.ids.append(perfil['estudiante_id'])
        self.assertEqual(perfil['documento_final'],d[-4:]);self.assertNotIn('codigo_institucional',perfil)
        self.assertEqual(self.identidad.autenticar_prueba_academica('CC',d,self.clave)['estudiante_id'],perfil['estudiante_id'])

    def test_completar_cuenta_heredada_conserva_id_y_cierra_sesion(self):
        i,d=self.crear(legado=True);self.contexto(i);self.editar(i,d,0);self.conn.commit()
        perfil=self.identidad.autenticar_prueba_academica('CC',d,self.clave);self.assertEqual(perfil['estudiante_id'],i)
        token=self.sesiones.abrir('estudiante',i,prueba_identidad=perfil['_prueba_identidad'])
        self.contexto(i);nuevo=self.numero();self.editar(i,nuevo,2);self.conn.commit()
        with self.assertRaises(self.sesiones.SesionInvalida):self.sesiones.validar('estudiante',i,token)
        self.assertIsNone(self.identidad.autenticar_prueba_academica('CC',d,self.clave))
        self.assertEqual(self.identidad.autenticar_prueba_academica('CC',nuevo,self.clave)['estudiante_id'],i)

    def test_no_permite_cambiar_documento_de_otro_estudiante(self):
        i,_=self.crear();otro,_=self.crear();self.contexto(i)
        with self.assertRaises(self.oracle.DatabaseError) as e:self.editar(otro,self.numero(),0)
        self.assertEqual(e.exception.args[0].code,20085)

    def test_version_obsoleta_y_documento_ocupado_no_sobrescriben(self):
        i,d=self.crear();_,ocupado=self.crear();self.contexto(i)
        with self.assertRaises(self.oracle.DatabaseError) as e:self.editar(i,self.numero(),99)
        self.assertEqual(e.exception.args[0].code,20303)
        with self.assertRaises(self.oracle.IntegrityError):self.editar(i,ocupado,0)
        self.conn.rollback()
        with self.conn.cursor() as cur:
            cur.execute('SELECT documento_huella FROM verificacion_estudiantes WHERE estudiante_id=:i',i=i)
            self.assertEqual(cur.fetchone()[0],self.identidad.huella_documento('CC',d)[0])

    def test_autorizacion_respeta_documento_y_cambio_revoca_credencial_anterior(self):
        import bcrypt
        i,d=self.crear();otro=self.numero();h,f=self.identidad.huella_documento('CC',d)
        with self.conn.cursor() as cur:
            out=cur.var(self.oracle.NUMBER)
            cur.execute("INSERT INTO administradores(usuario,nombre,contrasena) VALUES(:u,'Fixture documento','FIXTURE') RETURNING administrador_id INTO :i",u='DOC_'+uuid4().hex[:16],i=out)
            self.admin=int(out.getvalue()[0]);cur.callproc('pkg_auditoria.establecer_contexto',['ADMINISTRADOR',self.admin,None])
            hashed=bcrypt.hashpw(b'ClaveSinteticaDocumento!',bcrypt.gensalt()).decode()
            def autorizar(huella,final):
                valor=cur.var(self.oracle.NUMBER);valor.setvalue(0,i)
                cur.callproc('pkg_excepciones.autorizar',[valor,None,None,huella,'CC',final,hashed,'TECNICA','Fixture',1,0])
            otroh,otrof=self.identidad.huella_documento('CC',otro)
            with self.assertRaises(self.oracle.DatabaseError) as e:autorizar(otroh,otrof)
            self.assertEqual(e.exception.args[0].code,20313)
            autorizar(h,f)
        self.conn.commit();self.contexto(i);self.editar(i,otro,1);self.conn.commit()
        with self.conn.cursor() as cur:
            cur.execute('SELECT excepcion_activa,clave_hash,documento_huella FROM verificacion_estudiantes WHERE estudiante_id=:i',i=i)
            self.assertEqual(cur.fetchone(),(0,None,otroh))

    def test_actualizacion_administrativa_por_pool_restringido(self):
        from src.base_datos import administracion
        from src.servicios import documentos_estudiantes as documentos
        i,_=self.crear();nuevo=self.numero();token=secrets.token_urlsafe(32)
        with self.conn.cursor() as cur:
            out=cur.var(self.oracle.NUMBER)
            cur.execute("INSERT INTO administradores(usuario,nombre,contrasena) VALUES(:u,'Fixture documento','FIXTURE') RETURNING administrador_id INTO :i",u='DOC_'+uuid4().hex[:16],i=out)
            self.admin=int(out.getvalue()[0])
            cur.callproc('pkg_sesiones.abrir',['ADMINISTRADOR',self.admin,sha256(token.encode()).hexdigest()])
        self.conn.commit()
        with patch.object(administracion,'_actor',return_value=('administrador',self.admin,token)):
            documentos.guardar_administrativo(i,'CC',nuevo,version=0,comprobado=True)
        with self.conn.cursor() as cur:
            cur.execute('SELECT documento_huella FROM verificacion_estudiantes WHERE estudiante_id=:i',i=i)
            self.assertEqual(cur.fetchone()[0],self.identidad.huella_documento('CC',nuevo)[0])
