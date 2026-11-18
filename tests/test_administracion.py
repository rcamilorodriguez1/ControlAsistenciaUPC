import csv
from io import StringIO
import unittest
from unittest.mock import patch
from src.base_datos import administracion as admin
from src.utilidades.sesiones import iniciar_sesion, obtener_actor, cerrar_sesion, preparar_toma


class AdministracionTest(unittest.TestCase):
    def test_sesion_admin_no_guarda_hash_y_no_admite_capturas_docentes(self):
        estado = {}
        iniciar_sesion('administrador', {'administrador_id': 7, 'usuario': 'admin.prueba', 'nombre': 'Prueba', 'contrasena': 'NO_GUARDAR'}, estado)
        self.assertEqual(obtener_actor(estado)[:2], ('administrador', 7))
        self.assertNotIn('contrasena', estado['datos_administrador'])
        with self.assertRaises(PermissionError): preparar_toma(1, estado, clase_id=1)
        estado['admin_csv'] = b'informacion privada'
        cerrar_sesion('administrador', estado)
        self.assertIsNone(obtener_actor(estado)); self.assertNotIn('admin_csv', estado)

    def test_profesor_no_abre_pool_administrativo(self):
        with patch('src.utilidades.sesiones.obtener_actor', return_value=('profesor', 1, 'token')), patch.object(admin, 'obtener_pool_admin') as pool:
            with self.assertRaises(PermissionError): admin.cuentas('PROFESOR')
            with self.assertRaises(PermissionError): admin.materias()
            with self.assertRaises(PermissionError): admin.editar_profesor(1, 'docente', 'Docente', True, 'Motivo', version='0')
            pool.assert_not_called()

    def test_exportacion_no_interpreta_formulas_y_registra_preparacion(self):
        filas = [{'motivo': ' =HYPERLINK("prueba")', 'actor': '@ejemplo', 'numero': 3, 'nombre': 'Texto normal'}]
        with patch.object(admin, '_actor', return_value=('administrador', 1, 'token')), patch.object(admin, '_escritura') as escribir:
            contenido = admin.exportar_csv('GESTION', filas).decode('utf-8-sig')
        valores = list(csv.DictReader(StringIO(contenido)))[0]
        self.assertTrue(valores['motivo'].startswith("'")); self.assertTrue(valores['actor'].startswith("'"))
        self.assertEqual(valores['nombre'], 'Texto normal')
        self.assertEqual(filas[0]['actor'], '@ejemplo')
        escribir.assert_called_once_with('registrar_exportacion', ['GESTION', 1])

    def test_tipos_de_consulta_son_cerrados(self):
        with self.assertRaises(ValueError): admin.cuentas('ADMINISTRADOR')
        with self.assertRaises(ValueError): admin.cuentas('PROFESOR; DROP TABLE profesores')
