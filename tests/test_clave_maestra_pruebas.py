from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import MagicMock, patch

from src.servicios import clave_maestra_pruebas as claves
from src.servicios import sesiones_servidor as sesiones
from src.servicios import verificacion_identidad as identidad


class ClaveMaestraPruebasTest(unittest.TestCase):
    def setUp(self):
        self.clave = 'ClaveSinteticaAcademica!2026'
        p=patch.object(identidad,'_clave',return_value=b't'*32);p.start();self.addCleanup(p.stop)
        self.config = {'ESTUDIANTE_CLAVE_MAESTRA': self.clave,
            'ESTUDIANTE_CLAVE_MAESTRA_HASTA': (datetime.now(timezone.utc)+timedelta(hours=3)).isoformat()}
        p = patch.object(claves, 'obtener_configuracion', side_effect=lambda k, d=None:self.config.get(k,d))
        p.start(); self.addCleanup(p.stop)

    def test_desactivada_sin_secreto_vigencia_o_zona_horaria(self):
        for cambios in ({'ESTUDIANTE_CLAVE_MAESTRA':None}, {'ESTUDIANTE_CLAVE_MAESTRA':'corta'},
                        {'ESTUDIANTE_CLAVE_MAESTRA_HASTA':None}, {'ESTUDIANTE_CLAVE_MAESTRA_HASTA':'mal'},
                        {'ESTUDIANTE_CLAVE_MAESTRA_HASTA':'2099-01-01T12:00:00'},
                        {'ESTUDIANTE_CLAVE_MAESTRA_HASTA':'2020-01-01T00:00:00Z'}):
            anterior=self.config.copy()
            with self.subTest(cambios=list(cambios)):
                self.config.update(cambios)
                self.assertIsNone(claves.configuracion_pruebas())
                with self.assertRaises(PermissionError):claves.emitir_token_pruebas(7)
            self.config=anterior

    def test_clave_correcta_y_token_vinculados_a_cuenta_y_rol(self):
        config=claves.configuracion_pruebas()
        self.assertTrue(config.coincide(self.clave))
        for otra in ('incorrecta',None,self.clave+' ', 'x'*73):self.assertFalse(config.coincide(otra))
        token=claves.emitir_token_pruebas(7)
        self.assertLessEqual(len(token),128)
        self.assertTrue(claves.validar_token_pruebas('estudiante',7,token))
        self.assertFalse(claves.validar_token_pruebas('estudiante',8,token))
        self.assertFalse(claves.validar_token_pruebas('profesor',7,token))
        self.assertFalse(claves.validar_token_pruebas('administrador',7,token))

    def test_rotacion_cambio_de_vigencia_y_desactivacion_invalidan_token(self):
        for campo,valor in [('ESTUDIANTE_CLAVE_MAESTRA','OtraClaveSintetica!2026'),
                            ('ESTUDIANTE_CLAVE_MAESTRA_HASTA',(datetime.now(timezone.utc)+timedelta(hours=4)).isoformat()),
                            ('ESTUDIANTE_CLAVE_MAESTRA',None)]:
            anterior=self.config.copy();token=claves.emitir_token_pruebas(7)
            self.config[campo]=valor
            self.assertFalse(claves.validar_token_pruebas('estudiante',7,token))
            with self.assertRaises(sesiones.SesionInvalida):sesiones._parametros('estudiante',7,token)
            self.config=anterior

    def test_token_alterado_vencido_o_no_ascii_no_es_aceptado(self):
        config=claves.configuracion_pruebas();token=claves.emitir_token_pruebas(7)
        prefijo,vence,nonce,firma=token.split('.')
        pasado=str(int((datetime.now(timezone.utc)-timedelta(seconds=1)).timestamp()))
        for falso in ('prueba.sin.formato',token[:-1],'.'.join((prefijo,vence,nonce,'é'*64)),
                      '.'.join((prefijo,vence+'0',nonce,firma)),
                      '.'.join((prefijo,pasado,nonce,config.firma(7,pasado,nonce)))):
            self.assertFalse(claves.validar_token_pruebas('estudiante',7,falso))

    def test_tokens_normales_no_dependen_de_la_clave_academica(self):
        self.config.clear()
        for rol in ('profesor','estudiante','administrador'):
            self.assertEqual(len(sesiones._parametros(rol,7,'token-ordinario-sintetico')),3)

    def test_modo_apagado_no_consulta_cuentas(self):
        self.config.clear()
        with patch.object(identidad,'obtener_conexion') as conectar:
            self.assertIsNone(identidad.autenticar_prueba_academica('CC','123456789',self.clave))
        conectar.assert_not_called()

    def test_credencial_acepta_alumno_activo_sin_excepcion_y_audita_metodo(self):
        cur=MagicMock();cur.fetchone.side_effect=[(0,0,0),(7,'Fixture','TEST-7',0,1)]
        conn=MagicMock();conn.cursor.return_value.__enter__.return_value=cur
        with patch.object(identidad,'obtener_conexion') as conexion,patch.object(identidad,'_clave',return_value=b't'*32):
            conexion.return_value.__enter__.return_value=conn
            perfil=identidad.autenticar_prueba_academica('CC',' 123.456.789 ',self.clave)
        self.assertEqual(perfil['estudiante_id'],7)
        self.assertEqual(perfil['_prueba_identidad'].metodo,'PRUEBA_ACADEMICA')
        auditadas=[k for _,k in cur.execute.call_args_list if k.get('a')=='CREDENCIAL_VALIDADA']
        self.assertIn('PRUEBA_ACADEMICA',auditadas[0]['m'])
        self.assertNotIn(self.clave,str(cur.execute.call_args_list))

    def test_alumno_inactivo_desconocido_bloqueado_o_clave_erronea_no_accede(self):
        for fila,bloqueado,clave in [(None,0,self.clave),((7,'Fixture','TEST-7',0,0),0,self.clave),
                                     ((7,'Fixture','TEST-7',0,1),1,self.clave),
                                     ((7,'Fixture','TEST-7',0,1),0,'incorrecta')]:
            cur=MagicMock();cur.fetchone.side_effect=[(0,bloqueado,0),fila]
            conn=MagicMock();conn.cursor.return_value.__enter__.return_value=cur
            with patch.object(identidad,'obtener_conexion') as conexion:
                conexion.return_value.__enter__.return_value=conn
                self.assertIsNone(identidad.autenticar_prueba_academica('CC','123456789',clave))

    def test_documento_se_normaliza_y_rechaza_tipo_o_numero_invalido(self):
        cur=MagicMock();cur.fetchone.side_effect=[(0,0,0),(7,'Fixture','3456',0,1)]
        conn=MagicMock();conn.cursor.return_value.__enter__.return_value=cur
        with patch.object(identidad,'obtener_conexion') as conexion:
            conexion.return_value.__enter__.return_value=conn
            perfil=identidad.autenticar_prueba_academica('CC','00.123-456',self.clave)
            self.assertEqual((perfil['estudiante_id'],perfil['documento_final']),(7,'3456'))
            self.assertNotIn('codigo_institucional',perfil)
        for tipo,valor in [('CC','0'),('CC','123 OR 1=1'),('CC','１２３４５'),('OTRO','123456')]:
            with patch.object(identidad,'registrar_fallo_biometrico'),patch.object(identidad,'obtener_conexion') as conectar:
                self.assertIsNone(identidad.autenticar_prueba_academica(tipo,valor,self.clave))
                conectar.assert_not_called()

    def test_prueba_emitida_no_se_abre_si_cambia_configuracion(self):
        with patch.object(identidad,'_clave',return_value=b't'*32):
            prueba=identidad._emitir(7,'PRUEBA_ACADEMICA',0,claves.configuracion_pruebas().marca)
            cur=MagicMock();cur.fetchone.side_effect=[(0,None,0,0),(1,0)]
            conn=MagicMock();conn.cursor.return_value.__enter__.return_value=cur
            self.config.clear()
            with self.assertRaises(PermissionError):identidad.confirmar_en_conexion(conn,7,prueba)
            self.assertFalse(any('estado_verificacion=' in str(a[0]).lower() for a,_ in cur.execute.call_args_list))

    def test_estado_en_sesion_no_se_presenta_como_biometrico(self):
        from src.utilidades.sesiones import iniciar_sesion
        from src.servicios.verificacion_identidad import PruebaIdentidad
        estado={}
        perfil={'estudiante_id':7,'nombre':'Fixture','_prueba_identidad':PruebaIdentidad(7,'PRUEBA_ACADEMICA',0,0,'fixture')}
        iniciar_sesion('estudiante',perfil,estado)
        self.assertEqual(estado['datos_estudiante']['estado_verificacion'],'PRUEBA_ACADEMICA')
