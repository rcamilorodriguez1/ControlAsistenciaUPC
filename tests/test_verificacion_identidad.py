from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from src.servicios import verificacion_identidad as identidad
from src.servicios import excepciones_biometricas as gestion


class VerificacionIdentidadTest(unittest.TestCase):
    def setUp(self):
        p = patch.object(identidad, '_clave', return_value=b'c' * 32)
        p.start(); self.addCleanup(p.stop)

    def test_documento_canonico_conserva_ceros_y_distingue_tipo(self):
        self.assertEqual(identidad.normalizar_documento('CC', ' 00.123-456 '), '00123456')
        a, final = identidad.huella_documento('CC', '00.123-456')
        self.assertEqual((len(a), final), (64, '3456'))
        self.assertEqual(a, identidad.huella_documento('CC', '00123456')[0])
        self.assertNotEqual(a, identidad.huella_documento('CE', '00123456')[0])
        self.assertEqual(identidad.normalizar_documento('PA', 'ab-123456'), 'AB123456')
        for tipo, valor in [('CC', '12345X'), ('CC', '１２３４５'), ('CC', '1234'), ('OTRO', '123456'), ('PA', 'ab/12345')]:
            with self.subTest(tipo=tipo, valor=valor), self.assertRaises(ValueError):
                identidad.normalizar_documento(tipo, valor)

    def test_prueba_no_admite_otro_usuario_metodo_manipulacion_o_replay_tardio(self):
        prueba = identidad._emitir(7, 'EXCEPCION', 3, 'hash-sintetico')
        identidad._validar_prueba(prueba, 7)
        for modificada in (replace(prueba, estudiante_id=8), replace(prueba, metodo='BIOMETRIA'),
                           replace(prueba, version=4), replace(prueba, credencial='otra'),
                           replace(prueba, firma='f' * 64), None):
            with self.subTest(prueba=type(modificada)), self.assertRaises(PermissionError):
                identidad._validar_prueba(modificada, 7)
        with patch.object(identidad.time, 'time', return_value=prueba.emitida + 91), self.assertRaises(PermissionError):
            identidad._validar_prueba(prueba, 7)
        with patch.object(identidad.time, 'time', return_value=prueba.emitida - 1), self.assertRaises(PermissionError):
            identidad._validar_prueba(prueba, 7)

    def test_credencial_alternativa_exige_autorizacion_en_backend(self):
        with patch.object(gestion.datos, '_actor', side_effect=PermissionError('Denegado')), \
             patch.object(gestion, 'huella_documento') as huella, self.assertRaises(PermissionError):
            gestion.autorizar(7, 'CC', '123456789', 'ClaveSoloDePrueba!', 'TECNICA', 'EXP-1', 30, version=0, documento_comprobado=True)
        huella.assert_not_called()
        with patch.object(gestion.datos, '_actor'), patch.object(gestion, '_ejecutar') as escribir:
            with self.assertRaises(ValueError):
                gestion.autorizar(7, 'CC', '123456789', 'ClaveSoloDePrueba!', 'TECNICA', 'EXP-1', 30, version=0)
            with self.assertRaises(ValueError):
                gestion.autorizar(7, 'CC', '123456789', 'corta', 'TECNICA', 'EXP-1', 30, version=0, documento_comprobado=True)
            escribir.assert_not_called()

    def test_documento_malformado_audita_sin_buscar_cuenta(self):
        with patch.object(identidad, 'registrar_fallo_biometrico') as evento, \
             patch.object(identidad, 'obtener_conexion') as conexion:
            self.assertIsNone(identidad.autenticar_excepcion('CC', 'incorrecto', 'prueba'))
        conexion.assert_not_called()
        evento.assert_called_once_with('DOCUMENTO_INVALIDO', metodo='EXCEPCION')

    def test_sesion_de_otro_rol_impide_otra_verificacion_desde_el_backend(self):
        from src.servicios.autenticacion import ConflictoSesion
        with patch('src.servicios.autenticacion.get_script_run_ctx', return_value=object()), \
             patch('src.utilidades.sesiones.obtener_actor', return_value=('profesor', 7, 'token-sintetico')), \
             patch.object(identidad, 'obtener_conexion') as conectar:
            with self.assertRaises(ConflictoSesion):
                identidad.autenticar_excepcion('CC', '123456789', 'ClaveSintetica!')
            with self.assertRaises(ConflictoSesion):
                identidad.acreditar_biometria({'estudiante_id': 9})
        conectar.assert_not_called()

    def test_clave_perdida_no_se_regenera_si_existen_documentos(self):
        with TemporaryDirectory() as directorio:
            ruta = Path(directorio) / 'no-existe.key'
            cur = MagicMock()
            cur.fetchone.side_effect = [(1,), (1,)]
            conn = MagicMock()
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(identidad, 'ruta_clave', return_value=ruta), \
                 patch.object(identidad, 'obtener_conexion') as conexion:
                conexion.return_value.__enter__.return_value = conn
                with self.assertRaisesRegex(ValueError, 'original'):
                    identidad.preparar_clave()
            self.assertFalse(ruta.exists())
