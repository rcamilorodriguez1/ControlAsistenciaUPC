import unittest
from unittest.mock import patch

from src.servicios import documentos_estudiantes as documentos
from src.servicios import registro_estudiante as registro
from src.servicios.verificacion_identidad import huella_documento


class DocumentosEstudiantesTest(unittest.TestCase):
    def setUp(self):
        p=patch('src.servicios.verificacion_identidad._clave',return_value=b'd'*32)
        p.start();self.addCleanup(p.stop)

    def test_documento_igual_normalizado_y_tipo_diferente_no_se_confunden(self):
        self.assertEqual(huella_documento('CC','00.123-456'),huella_documento('CC','00123456'))
        self.assertNotEqual(huella_documento('CC','00123456')[0],huella_documento('TI','00123456')[0])
        self.assertEqual(documentos.etiqueta_documento('CC','3456'),'CC · ****3456')
        self.assertEqual(documentos.etiqueta_documento(),'Documento pendiente')

    def test_otro_rol_no_consulta_ni_modifica_documento_propio(self):
        for actor in (None,('profesor',7,'token'),('administrador',7,'token')):
            with patch.object(documentos,'obtener_actor',return_value=actor),patch.object(documentos.gestion,'ejecutar') as guardar:
                with self.assertRaises(PermissionError):documentos.guardar_propio('CC','123456789',version=0,comprobado=True)
                with self.assertRaises(PermissionError):documentos.consultar_propio()
                guardar.assert_not_called()

    def test_guardado_propio_envia_hmac_no_documento_completo_y_exige_confirmacion(self):
        with patch.object(documentos,'obtener_actor',return_value=('estudiante',7,'token')),patch.object(documentos.gestion,'ejecutar') as guardar:
            with self.assertRaises(ValueError):documentos.guardar_propio('CC','123456789',version=0)
            guardar.assert_not_called()
            documentos.guardar_propio('CC','123.456.789',version=2,comprobado=True)
        guardar.assert_called_once_with('actualizar_documento',[7,huella_documento('CC','123456789')[0],'CC','6789',2])
        self.assertNotIn('123456789',str(guardar.call_args))

    def test_administracion_pasa_por_su_cuenta_restringida(self):
        with patch.object(documentos.administracion,'_actor') as actor,patch.object(documentos.administracion,'_escritura') as guardar:
            documentos.guardar_administrativo(7,'CC','123456789',version=0,comprobado=True)
        actor.assert_called_once()
        self.assertEqual(guardar.call_args.args[0],'actualizar_documento')

    def test_documento_invalido_se_rechaza_antes_de_procesar_foto(self):
        for tipo,numero in [('OTRO','123456789'),('CC','abc'),('CC','１２３４５')]:
            with patch.object(registro,'leer_foto_registro') as leer,patch.object(registro,'crear_estudiante') as crear:
                with self.assertRaises(ValueError):registro.registrar_estudiante('Alumno',None,tipo_documento=tipo,documento=numero)
                leer.assert_not_called();crear.assert_not_called()

    def test_sesion_solo_conserva_documento_enmascarable(self):
        from src.utilidades.sesiones import iniciar_sesion
        estado={}
        iniciar_sesion('estudiante',{'estudiante_id':7,'nombre':'Alumno','tipo_documento':'CC',
            'documento_final':'6789','documento':'123456789','documento_huella':'no-guardar','codigo_institucional':'LEGADO'},estado)
        datos=estado['datos_estudiante']
        self.assertEqual((datos['tipo_documento'],datos['documento_final']),('CC','6789'))
        for campo in ('documento','documento_huella','codigo_institucional'):self.assertNotIn(campo,datos)
