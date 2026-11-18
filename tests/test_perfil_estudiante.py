import unittest
from copy import deepcopy
from datetime import date
from unittest.mock import patch

from soporte_perfil import filas_perfil
from src.servicios.perfil_estudiante import (
    construir_perfil, cargar_perfil_estudiante, estado_dia, estado_porcentaje,
)
from src.pantallas.perfil_estudiante import html_calendario


class PerfilEstudianteTest(unittest.TestCase):
    def test_acumulado_ponderado_y_matriculas_actuales(self):
        perfil = construir_perfil(filas_perfil(7))
        self.assertEqual((perfil['asistidas'], perfil['ausencias'], perfil['total']), (21, 5, 26))
        self.assertAlmostEqual(perfil['porcentaje'], 21 / 26 * 100)
        self.assertEqual(perfil['total_materias'], 4)
        materias = {m['materia_id']: m for m in perfil['materias']}
        self.assertEqual(materias[10]['porcentaje'], 80)
        self.assertEqual(materias[20]['estado']['clave'], 'excelente')
        self.assertEqual(materias[30]['estado']['clave'], 'riesgo')
        self.assertIsNone(materias[40]['porcentaje'])
        self.assertFalse(materias[99]['matriculada'])

    def test_clases_duplicadas_no_inflan_totales_y_conflictos_se_rechazan(self):
        filas = filas_perfil()
        self.assertEqual(construir_perfil(filas + [deepcopy(filas[0])])['total'], 26)
        duplicada = {**filas[0], 'presente': 0}
        with self.assertRaises(ValueError): construir_perfil(filas + [duplicada])

    def test_sin_materias_sin_registros_y_cero_por_ciento_son_diferentes(self):
        fila = {**filas_perfil()[0], 'materia_id': None, 'clase_id': None}
        perfil = construir_perfil([fila])
        self.assertEqual(perfil['total_materias'], 0)
        self.assertEqual(perfil['materias'], [])
        self.assertIsNone(perfil['porcentaje'])
        filas = filas_perfil()
        for f in filas:
            if f['clase_id'] is not None: f['presente'] = 0
        perfil = construir_perfil(filas)
        self.assertEqual(perfil['porcentaje'], 0)
        self.assertEqual(perfil['estado']['clave'], 'riesgo')

    def test_no_admite_registros_pendientes_como_ausencias(self):
        filas = filas_perfil()
        filas[0]['presente'] = None
        with self.assertRaises(ValueError): construir_perfil(filas)

    def test_dia_mixto_ausencia_y_dia_sin_registros(self):
        perfil = construir_perfil(filas_perfil())
        self.assertEqual(estado_dia(perfil['dias'][date(2026, 11, 1)]), 'presente')
        self.assertEqual(estado_dia(perfil['dias'][date(2026, 11, 7)]), 'mixto')
        self.assertEqual(estado_dia(perfil['dias'][date(2026, 11, 10)]), 'ausente')
        self.assertEqual(estado_dia([]), 'sin-registros')

    def test_calendario_usa_fecha_de_clase_en_colombia(self):
        fila = {**filas_perfil()[0], 'fecha_clase': '2026-11-08T04:30:00+00:00'}
        perfil = construir_perfil([fila])
        self.assertIn(date(2026, 11, 7), perfil['dias'])
        html = html_calendario(date(2026, 11, 1), perfil['dias'], date(2026, 11, 17))
        self.assertIn('data-dia="2026-11-07" data-estado="presente"', html)
        self.assertIn('data-dia="2026-11-08" data-estado="sin-registros"', html)
        self.assertNotIn('<script', html)

    def test_mes_bisiesto_y_dias_fuera_del_mes(self):
        html = html_calendario(date(2024, 2, 1), {}, date(2024, 2, 29))
        self.assertEqual(html.count('data-dia='), 29)
        self.assertIn('aria-current="date"', html)
        self.assertNotIn('data-dia="2024-03', html)

    def test_umbrales_y_estado_sin_datos(self):
        for p, esperado in [(None, 'sin-registros'), (0, 'riesgo'), (79.99, 'riesgo'),
                            (80, 'aceptable'), (89.99, 'aceptable'), (90, 'excelente'), (100, 'excelente')]:
            self.assertEqual(estado_porcentaje(p)['clave'], esperado)

    def test_servicio_rechaza_otros_roles_antes_de_consultar(self):
        for actor in (None, ('profesor', 7, 'token'), ('administrador', 7, 'token')):
            with patch('src.servicios.perfil_estudiante.obtener_actor', return_value=actor), \
                 patch('src.servicios.perfil_estudiante.consultar_datos') as consultar:
                with self.assertRaises(PermissionError): cargar_perfil_estudiante()
                consultar.assert_not_called()

    def test_servicio_no_acepta_perfil_de_otro_estudiante(self):
        with patch('src.servicios.perfil_estudiante.obtener_actor', return_value=('estudiante', 7, 'token')), \
             patch('src.servicios.perfil_estudiante.consultar_datos', return_value=filas_perfil(8)) as consultar:
            with self.assertRaises(PermissionError): cargar_perfil_estudiante()
            consultar.assert_called_once_with(7)
        filas = filas_perfil(7)
        filas[1]['estudiante_id'] = 8
        with self.assertRaises(PermissionError): construir_perfil(filas)
