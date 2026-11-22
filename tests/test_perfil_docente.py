from datetime import datetime, date
from html.parser import HTMLParser
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from src.servicios.perfil_docente import construir_perfil, cargar_perfil_docente
from src.utilidades.fecha_hora import ZONA_HORARIA_COLOMBIA


def filas():
    base = dict(profesor_id=1, nombre_profesor='Docente <de prueba>', usuario='fixture',
        materia_id=10, nombre_materia='<img src=x onerror=alert(1)>', codigo_materia='BD-1',
        seccion='A', materia_activa=1, total_estudiantes=2, clase_id=4, estado='BORRADOR',
        fecha_clase='2026-12-02T09:00:00-05:00')
    return [base, dict(base, clase_id=5, estado='CONFIRMADA', fecha_clase='2026-11-01T09:00:00-05:00'),
        dict(base, materia_id=20, nombre_materia='Histórica', materia_activa=0, clase_id=6)]


class PerfilDocenteTest(unittest.TestCase):
    def test_agenda_deduplica_y_separa_futuras_confirmadas_y_materias_archivadas(self):
        ahora = datetime(2026, 11, 22, tzinfo=ZONA_HORARIA_COLOMBIA)
        perfil = construir_perfil(filas()+filas()[:1], ahora)
        self.assertEqual(len(perfil['materias']), 2)
        self.assertEqual(perfil['total_activas'], 1)
        self.assertEqual(perfil['confirmadas'], 1)
        self.assertEqual([c['clase_id'] for c in perfil['proximas']], [4])
        self.assertEqual(len(perfil['dias'][date(2026, 12, 2)]), 2)

    def test_cuenta_sin_materias_y_fuera_del_horario_no_infiere_asistencia(self):
        perfil = construir_perfil([dict(filas()[0], materia_id=None)])
        self.assertEqual(perfil['materias'], [])
        self.assertEqual(perfil['proximas'], [])
        perfil = construir_perfil(filas(), datetime(2027, 1, 1, tzinfo=ZONA_HORARIA_COLOMBIA))
        self.assertEqual(perfil['proximas'], [])
        self.assertEqual(perfil['confirmadas'], 1)

    def test_rechaza_mezcla_de_identidad_y_consulta_de_otro_rol(self):
        with self.assertRaises(PermissionError):
            construir_perfil(filas()+[dict(filas()[0], profesor_id=2)])
        with patch('src.servicios.perfil_docente.obtener_actor', return_value=('estudiante', 1, 't')), \
             patch('src.servicios.perfil_docente.consultar_datos') as consulta:
            with self.assertRaises(PermissionError): cargar_perfil_docente()
            consulta.assert_not_called()
        with patch('src.servicios.perfil_docente.obtener_actor', return_value=('profesor', 2, 't')), \
             patch('src.servicios.perfil_docente.consultar_datos', return_value=filas()):
            with self.assertRaises(PermissionError): cargar_perfil_docente()

    def test_calendario_escapa_nombres_y_admite_mes_vacio(self):
        from src.pantallas.perfil_docente import html_calendario_docente
        perfil = construir_perfil(filas())
        html = html_calendario_docente(date(2026, 12, 1), perfil['dias'])
        class Etiquetas(HTMLParser):
            def __init__(self): super().__init__(); self.tags = []
            def handle_starttag(self, tag, attrs): self.tags.append(tag)
        parser = Etiquetas(); parser.feed(html)
        self.assertNotIn('img', parser.tags)
        self.assertIn('&lt;img', html)
        self.assertIn('Agenda docente de febrero 2028', html_calendario_docente(date(2028, 2, 1), {}))

    def test_rutas_separan_agenda_configuracion_y_portal(self):
        from src.utilidades.sesiones import iniciar_sesion
        from streamlit.util import calc_hash
        estado = {}
        iniciar_sesion('profesor', dict(profesor_id=1, nombre='Docente', usuario='fixture'), estado)
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'principal.py'), default_timeout=40)
        for k, v in estado.items(): app.session_state[k] = v
        app._page_hash = calc_hash('mi-perfil-docente')
        with patch('src.servicios.sesiones_servidor.validar'), \
             patch('src.servicios.perfil_docente.consultar_datos', return_value=filas()), \
             patch('src.componentes.gestion_cuenta.obtener_materias_profesor', return_value=[]):
            app.run()
            self.assertFalse(app.exception)
            self.assertTrue(any(h.value == 'Agenda de clases' for h in app.subheader))
            self.assertFalse(any(e.label == 'Administrar cuenta e historial' for e in app.expander))
            app._page_hash = app.session_state['_pagina_configuracion_profesor']._script_hash
            app.run()
            self.assertFalse(app.exception)
            self.assertTrue(any(e.label == 'Administrar cuenta e historial' for e in app.expander))
            self.assertFalse(any(h.value == 'Agenda de clases' for h in app.subheader))
            self.assertEqual(app.session_state['sesion_token'], estado['sesion_token'])
