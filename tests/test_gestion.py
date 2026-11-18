import unittest
from unittest.mock import patch
from src.servicios.validaciones import texto, codigo, usuario, clave
from src.servicios.cuentas import autorizar_alta_docente
from src.utilidades import sesiones


class ReglasTest(unittest.TestCase):
    def test_normaliza_identificadores_y_acota_campos(self):
        self.assertEqual(codigo(' abc-123 '), 'ABC-123')
        self.assertEqual(usuario(' Docente_1 '), 'docente_1')
        self.assertEqual(texto(' Jose\u0301 ', 'Nombre', 10), 'José')
        for valor in ['', 'ABC DEF', '../x', 'ÁBC', 'A' * 51]:
            with self.assertRaises(ValueError): codigo(valor)
        with self.assertRaises(ValueError): texto('nombre\x00', 'Nombre', 200)

    def test_clave_bcrypt_limite_en_bytes_y_autorizacion_docente(self):
        clave('á' * 36)
        for valor in ['corta', 'á' * 37, 'A' * 73, 'abcdefgh\x00']:
            with self.assertRaises(ValueError): clave(valor)
        with patch('src.servicios.cuentas.obtener_configuracion', return_value='privado'):
            autorizar_alta_docente('privado')
            with self.assertRaises(ValueError): autorizar_alta_docente('otro')

    def test_caducidad_inactividad_y_duracion_total_invalidan_capturas(self):
        for inicio, ultimo, ahora in [(1000, 1000, 2800), (1000, 29799, 29800)]:
            estado = {}
            with patch.object(sesiones.time, 'time', return_value=inicio):
                sesiones.iniciar_sesion('profesor', {'profesor_id': 1, 'nombre': 'Docente', 'usuario': 'docente'}, estado)
                contexto = sesiones.preparar_toma(1, estado, clase_id=1)
            estado['sesion_actividad_en'] = ultimo
            with patch.object(sesiones.time, 'time', return_value=ahora):
                self.assertIsNone(sesiones.obtener_actor(estado))
                self.assertFalse(sesiones.contexto_vigente(contexto, estado))
                sesiones.inicializar_sesion(estado)
                self.assertFalse(estado['sesion_iniciada'])
                self.assertNotIn('contexto_asistencia', estado)

    def test_campos_invalidos_no_abren_conexion(self):
        from src.base_datos import bd
        with patch.object(bd, 'ejecutar_con_reintentos') as ejecutar:
            with self.assertRaises(ValueError): bd.crear_profesor('docente', 'corta', 'Docente')
            with self.assertRaises(ValueError): bd.crear_estudiante('Alumno', [.1] * 128)
            ejecutar.assert_not_called()
