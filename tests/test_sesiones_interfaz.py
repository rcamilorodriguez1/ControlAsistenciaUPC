"""Regresiones de navegación y diálogos: BD e IA sustituidas, sin escribir datos reales."""

from io import BytesIO
import unittest
import wave
from unittest.mock import patch

from PIL import Image
import numpy as np
from streamlit.testing.v1 import AppTest

from src.utilidades.sesiones import iniciar_sesion, preparar_toma, guardar_resultado
from src.utilidades.imagenes import FotoAsistencia


class SesionesInterfazTest(unittest.TestCase):
    def setUp(self):
        from soporte_sesiones import simular_sesiones
        simular_sesiones(self)
        self.parches = [
            patch('src.componentes.gestion_cuenta.obtener_materias_profesor', return_value=[]),
            patch('src.pantallas.pantalla_profesor.obtener_resumen_profesor', return_value={
                'total_materias': 2, 'total_estudiantes': 2, 'asistencia_promedio': 0}),
            patch('src.pantallas.pantalla_profesor.obtener_materias_profesor', return_value=[
                {'materia_id': 10, 'nombre': 'Materia A', 'codigo_materia': 'A', 'seccion': '1',
                 'profesor_id': 1, 'total_estudiantes': 1, 'total_clases': 0},
                {'materia_id': 20, 'nombre': 'Materia B', 'codigo_materia': 'B', 'seccion': '1',
                 'profesor_id': 1, 'total_estudiantes': 1, 'total_clases': 0}]),
            patch('src.componentes.selector_clase.obtener_clases_profesor', side_effect=lambda m, p: [
                {'clase_id': 100 if m == 10 else 200, 'materia_id': m, 'estado': 'BORRADOR',
                 'origen': 'PENDIENTE', 'lote_legado': 0, 'fecha_hora': '2026-11-11T08:00:00-05:00'}]),
            patch('src.componentes.dialogo_asistencia_voz.obtener_estudiantes_matriculados',
                  side_effect=lambda m: [{'estudiante_id': 7 if m == 10 else 8, 'nombre': 'Alumno',
                                          'embedding_voz': [1.0], 'embedding_facial': None}]),
            patch('src.pantallas.pantalla_estudiante.obtener_resumen_estudiante', return_value={
                'total_materias': 0, 'total_clases': 0, 'asistencia_promedio': 0}),
            patch('src.pantallas.pantalla_estudiante.obtener_materias_estudiante', return_value=[]),
            patch('src.pantallas.pantalla_estudiante.obtener_asistencia_estudiante', return_value=[]),
        ]
        for parche in self.parches:
            parche.start()
            self.addCleanup(parche.stop)
        self.at = AppTest.from_file('../principal.py', default_timeout=45)

    def boton(self, etiqueta):
        return next(b for b in self.at.button if b.label == etiqueta)

    def cargar(self, estado):
        from streamlit.util import calc_hash
        self.at._page_hash = calc_hash({'profesor': 'docente', 'estudiante': 'estudiante', 'administrador': 'administracion'}[estado['rol_usuario']])
        for clave, valor in estado.items():
            self.at.session_state[clave] = valor

    def profesor(self, pendiente=False):
        estado = {}
        iniciar_sesion('profesor', {'profesor_id': 1, 'usuario': 'p1', 'nombre': 'Profesor'}, estado)
        contexto = preparar_toma(10, estado, clase_id=100)
        if pendiente:
            estado['imagenes_asistencia'] = [Image.new('RGB', (8, 8))]
            estado['claves_subidas_procesadas'] = {'huella'}
            guardar_resultado(contexto, [{'Nombre': 'Resultado de materia A', 'Estado': 'Presente', 'Puntaje': '0.92'}],
                [{'materia_id': 10, 'estudiante_id': 7, 'presente': True,
                  'fecha_hora': '2026-11-11T10:00:00-05:00'}], 'voz', estado)
        self.cargar(estado)
        return contexto

    def comprobar(self):
        self.assertEqual([e.message for e in self.at.exception], [])

    def test_acceso_y_registro_cambian_con_un_solo_click(self):
        self.at.run()
        self.boton('Portal del Profesor').click().run()
        self.boton('Registrarme en su lugar').click().run()
        self.comprobar()
        self.assertIn('Registra tu perfil de profesor', [h.value for h in self.at.header])
        self.boton('Iniciar Sesión en su lugar').click().run()
        self.assertIn('Inicia sesión con tu contraseña', [h.value for h in self.at.header])

    def test_inicio_conserva_materia_clase_y_capturas_pendientes(self):
        self.profesor();self.at.run()
        self.at.selectbox[0].select(20).run()
        self.at.selectbox[1].select(200).run()
        token=self.at.session_state['sesion_token']
        self.at.session_state['imagenes_asistencia']=[Image.new('RGB',(8,8))]
        self.boton('Gestionar Materias').click().run()
        self.at._page_hash=self.at.session_state['_pagina_inicio']._script_hash
        self.at.run();self.comprobar()
        self.assertEqual(self.at.session_state['sesion_token'],token)
        self.assertEqual(self.at.session_state['contexto_asistencia']['materia_id'],20)
        self.assertEqual(self.at.session_state['contexto_asistencia']['clase_id'],200)
        self.assertEqual(len(self.at.session_state['imagenes_asistencia']),1)

    def test_login_y_logout_borran_password_y_trabajo_pendiente(self):
        self.at.run()
        self.boton('Portal del Profesor').click().run()
        self.at.text_input[0].input('p1')
        self.at.text_input[1].input('clave-de-prueba')
        with patch('src.pantallas.pantalla_profesor.iniciar_sesion_profesor', return_value={
                'profesor_id': 1, 'usuario': 'p1', 'nombre': 'Profesor', 'contrasena': 'hash'}):
            self.boton('Iniciar Sesión').click().run()
        self.comprobar()
        self.assertNotIn('contrasena', self.at.session_state['datos_profesor'])
        token = self.at.session_state['sesion_token']
        self.at.session_state['imagenes_asistencia'] = [Image.new('RGB', (8, 8))]
        self.at.session_state['resultado_asistencia'] = {'id': 'viejo'}
        self.at.button(key='loginbackbtn').click().run()
        self.comprobar()
        estado = self.at.session_state.to_dict()
        self.assertFalse(estado['sesion_iniciada'])
        self.assertIsNone(estado['rol_usuario'])
        self.assertNotIn('datos_profesor', estado)
        self.assertNotIn('resultado_asistencia', estado)
        self.assertNotIn('imagenes_asistencia', estado)
        self.assertNotEqual(token, estado['sesion_token'])
        self.assertTrue(all(i.value == '' for i in self.at.text_input))
        self.assertFalse(any('clave-de-prueba' == v for v in estado.values() if isinstance(v, str)))

    def test_resultado_de_voz_no_pasa_a_otra_materia(self):
        self.profesor(pendiente=True)
        self.at.run()
        self.at.selectbox[0].select(20).run()
        self.at.selectbox[1].select(200).run()
        self.boton('Usar Asistencia por Voz').click().run()
        self.comprobar()
        self.assertEqual(self.at.session_state['materia_asistencia_id'], 20)
        self.assertEqual(self.at.session_state['imagenes_asistencia'], [])
        self.assertEqual(len(self.at.dataframe), 0)
        self.assertFalse(any(b.label == 'Confirmar y Aprobar' for b in self.at.button))

    def test_voz_pendiente_de_la_misma_materia_se_confirma_una_vez(self):
        self.profesor(pendiente=True)
        self.at.run()
        self.boton('Usar Asistencia por Voz').click().run()
        self.assertEqual(len(self.at.data_editor), 1)
        with patch('src.servicios.asistencia.crear_asistencia', return_value=1) as guardar:
            # AppTest reejecuta el script completo, sin el rerun parcial del navegador.
            # Mantener abierto el diálogo permite comprobar su confirmación en ese modo.
            self.boton('Usar Asistencia por Voz').click()
            self.boton('Confirmar y Aprobar').click().run()
            guardar.assert_called_once()
            self.assertEqual(guardar.call_args.kwargs['profesor_id'], 1)
            self.assertEqual(guardar.call_args.kwargs['clase_id'], 100)
            self.assertEqual(guardar.call_args.kwargs['origen'], 'voz')
        self.comprobar()
        self.assertNotIn('resultado_asistencia', self.at.session_state)
        self.assertEqual(self.at.session_state['imagenes_asistencia'], [])
        self.assertEqual(self.at.session_state['claves_subidas_procesadas'], set())

    def test_perfil_residual_no_abre_panel_sin_sesion(self):
        self.profesor()
        self.at.session_state['sesion_iniciada'] = False
        with patch('src.pantallas.pantalla_profesor.obtener_resumen_profesor') as resumen:
            self.at.run()
            resumen.assert_not_called()
        self.comprobar()
        self.assertIn('Inicia sesión con tu contraseña', [h.value for h in self.at.header])

    def test_editor_exige_motivo_y_envia_correccion_antes_de_confirmar(self):
        self.profesor(pendiente=True)
        self.at.run()
        self.boton('Usar Asistencia por Voz').click().run()
        clave = self.at.data_editor[0].key
        self.at.session_state[clave] = {'edited_rows': {0: {'Decisión': 'Ausente'}}, 'added_rows': [], 'deleted_rows': []}
        with patch('src.servicios.asistencia.crear_asistencia', return_value=1) as guardar:
            self.boton('Usar Asistencia por Voz').click()
            self.boton('Confirmar y Aprobar').click().run()
            self.comprobar()
            guardar.assert_not_called()
            self.assertTrue(any('motivo' in w.value for w in self.at.warning))
            self.assertIn('resultado_asistencia', self.at.session_state)
            self.at.session_state[clave] = {'edited_rows': {0: {'Decisión': 'Ausente', 'Motivo': 'Revisión en clase'}},
                                           'added_rows': [], 'deleted_rows': []}
            self.boton('Usar Asistencia por Voz').click()
            self.boton('Confirmar y Aprobar').click().run()
            self.comprobar()
            guardar.assert_called_once()
            registro = guardar.call_args.args[0][0]
            self.assertTrue(registro['presente_detectado'])
            self.assertFalse(registro['presente'])
            self.assertEqual(registro['motivo_correccion'], 'Revisión en clase')

    def test_clase_confirmada_no_admite_otra_captura_o_propuesta(self):
        self.profesor(pendiente=True)
        with patch('src.componentes.selector_clase.obtener_clases_profesor', return_value=[
            {'clase_id': 100, 'materia_id': 10, 'estado': 'CONFIRMADA', 'origen': 'FACIAL',
             'lote_legado': 0, 'fecha_hora': '2026-11-11T08:00:00-05:00'}]):
            self.at.run()
        self.comprobar()
        self.assertNotIn('resultado_asistencia', self.at.session_state)
        self.assertEqual(self.at.session_state['imagenes_asistencia'], [])
        self.assertFalse(any(b.label in ('Agregar Fotos', 'Ejecutar Análisis Facial', 'Usar Asistencia por Voz') for b in self.at.button))

    def test_crear_o_abrir_horario_selecciona_la_clase_devuelta(self):
        self.profesor()
        self.at.run()
        self.at.selectbox[1].select(None).run()
        self.assertFalse(any(b.label == 'Agregar Fotos' for b in self.at.button))
        with patch('src.componentes.selector_clase.abrir_clase', return_value=100) as abrir:
            self.boton('Crear o abrir este horario').click().run()
            abrir.assert_called_once()
            self.assertEqual(abrir.call_args.args[:2], (10, 1))
            self.assertIsNotNone(abrir.call_args.args[2].tzinfo)
        self.comprobar()
        self.assertEqual(self.at.session_state['contexto_asistencia']['clase_id'], 100)
        self.assertTrue(any(b.label == 'Agregar Fotos' for b in self.at.button))

    def test_reporte_separa_clases_con_analisis_en_el_mismo_segundo(self):
        self.profesor()
        self.at.run()
        filas = [
            {'clase_id': c, 'fecha_hora': '2026-11-11T10:00:00.123456-05:00',
             'fecha_clase': '2026-11-11T08:00:00.000000-05:00', 'presente': p,
             'origen': 'LEGADO', 'corregido_manual': False,
             'materia': {'nombre': 'Materia A', 'codigo_materia': 'A'}}
            for c, p in [(100, True), (100, False), (101, True)]]
        with patch('src.pantallas.pantalla_profesor.obtener_asistencia_profesor', return_value=filas):
            self.boton('Registros de Asistencia').click().run()
        self.comprobar()
        tabla = self.at.dataframe[0].value
        self.assertEqual(set(tabla['Clase']), {100, 101})
        self.assertEqual(len(tabla), 2)

    def test_audio_nuevo_invalida_resultado_anterior_sin_analizar(self):
        self.profesor(pendiente=True)
        self.at.run()
        self.boton('Usar Asistencia por Voz').click().run()
        archivo = BytesIO()
        with wave.open(archivo, 'wb') as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            audio.writeframes(b'\0' * 3200)
        self.boton('Usar Asistencia por Voz').click()
        self.at.audio_input[0].upload('nueva.wav', archivo.getvalue()).run()
        self.comprobar()
        self.assertNotIn('resultado_asistencia', self.at.session_state)
        self.assertEqual(len(self.at.dataframe), 0)
        self.assertFalse(any(b.label == 'Confirmar y Aprobar' for b in self.at.button))

    def test_foto_comprimida_muestra_miniatura_y_analiza_el_original(self):
        self.profesor()
        datos, previa = BytesIO(), BytesIO()
        Image.new('RGB', (800, 600), 'red').save(datos, format='PNG')
        Image.new('RGB', (80, 60), 'blue').save(previa, format='JPEG')
        self.at.session_state['imagenes_asistencia'] = [FotoAsistencia(datos.getvalue(), previa.getvalue())]
        with patch('src.pantallas.pantalla_profesor.obtener_estudiantes_matriculados', return_value=[
                {'estudiante_id': 7, 'nombre': 'Alumno', 'embedding_facial': [0.1] * 128}]), \
                patch('src.pantallas.pantalla_profesor.predecir_asistencia', return_value=({7: True}, [7], 1)) as analizar:
            self.at.run()
            self.comprobar()
            self.boton('Ejecutar Análisis Facial').click().run()
        self.comprobar()
        recibida = analizar.call_args.args[0]
        self.assertEqual(recibida.shape, (600, 800, 3))
        np.testing.assert_array_equal(recibida[0, 0], [255, 0, 0])
        self.assertEqual(analizar.call_args.kwargs['permitidos'], {7})
        self.assertTrue(self.at.session_state['resultado_asistencia']['registros'][0]['presente'])

    def grabar_audio_de_prueba(self):
        archivo = BytesIO()
        with wave.open(archivo, 'wb') as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            audio.writeframes(b'\0' * 3200)
        self.boton('Usar Asistencia por Voz').click()
        self.at.audio_input[0].upload('prueba.wav', archivo.getvalue()).run()

    def test_audio_fallido_o_contrato_antiguo_no_permite_confirmar(self):
        self.profesor(pendiente=True)
        self.at.run()
        self.boton('Usar Asistencia por Voz').click().run()
        self.grabar_audio_de_prueba()
        # Regresión exacta: el antiguo {} de error no puede interpretarse como todos ausentes.
        with patch('src.componentes.dialogo_asistencia_voz.procesar_audio_masivo', return_value={}), patch(
                'src.servicios.asistencia.crear_asistencia') as guardar:
            self.boton('Usar Asistencia por Voz').click()
            self.boton('Analizar Audio').click().run()
            self.comprobar()
            self.assertTrue(any('Análisis fallido' in e.value for e in self.at.error))
            self.assertFalse(any(b.label == 'Confirmar y Aprobar' for b in self.at.button))
            registros = self.at.session_state['resultado_asistencia']['registros']
            self.assertTrue(all(r['presente'] is None and r['estado_deteccion'] == 'ANALISIS_FALLIDO' for r in registros))
            guardar.assert_not_called()

    def test_foto_sin_muestra_facial_no_se_convierte_en_ausencia(self):
        self.profesor(pendiente=True)
        self.at.run()
        with patch('src.pantallas.pantalla_profesor.obtener_estudiantes_matriculados', return_value=[
                {'estudiante_id': 7, 'nombre': 'Sin rostro registrado', 'embedding_facial': None}]), patch(
                'src.pantallas.pantalla_profesor.predecir_asistencia', return_value=({}, [], 0)):
            self.boton('Ejecutar Análisis Facial').click().run()
        self.comprobar()
        tabla = self.at.data_editor[0].value
        self.assertEqual(tabla.iloc[0]['Detección'], 'Sin muestra')
        self.assertEqual(tabla.iloc[0]['Decisión'], 'Pendiente')
        self.assertIsNone(self.at.session_state['resultado_asistencia']['registros'][0]['presente'])

    def test_excepcion_facial_descarta_propuesta_anterior_sin_generar_ausencias(self):
        self.profesor(pendiente=True)
        self.at.run()
        with patch('src.pantallas.pantalla_profesor.obtener_estudiantes_matriculados', return_value=[
                {'estudiante_id': 7, 'nombre': 'Alumno', 'embedding_facial': [1.]}]), patch(
                'src.pantallas.pantalla_profesor.predecir_asistencia', side_effect=RuntimeError('fallo de modelo')):
            self.boton('Ejecutar Análisis Facial').click().run()
        self.comprobar()
        self.assertNotIn('resultado_asistencia', self.at.session_state)
        self.assertTrue(any('fallido' in e.value for e in self.at.error))

    def test_sin_muestra_queda_pendiente_hasta_resolucion_manual_con_motivo(self):
        from src.canalizaciones.canalizacion_voz import ResultadoAudio
        estudiantes = [{'estudiante_id': 7, 'nombre': 'Con voz', 'embedding_voz': [1.]},
                       {'estudiante_id': 9, 'nombre': 'Sin voz', 'embedding_voz': None}]
        self.profesor()
        self.at.run()
        with patch('src.componentes.dialogo_asistencia_voz.obtener_estudiantes_matriculados', return_value=estudiantes), patch(
                'src.componentes.dialogo_asistencia_voz.procesar_audio_masivo', return_value=ResultadoAudio('COMPLETADO', {7: 0.9})), patch(
                'src.servicios.asistencia.crear_asistencia', return_value=2) as guardar:
            self.boton('Usar Asistencia por Voz').click().run()
            self.grabar_audio_de_prueba()
            self.boton('Usar Asistencia por Voz').click()
            self.boton('Analizar Audio').click().run()
            self.comprobar()
            tabla = self.at.data_editor[0].value
            self.assertEqual(list(tabla['Detección']), ['Presente', 'Sin muestra'])
            self.assertEqual(list(tabla['Decisión']), ['Presente', 'Pendiente'])
            self.boton('Usar Asistencia por Voz').click()
            self.boton('Confirmar y Aprobar').click().run()
            self.comprobar()
            guardar.assert_not_called()
            clave = self.at.data_editor[0].key
            self.at.session_state[clave] = {'edited_rows': {1: {'Decisión': 'Ausente', 'Motivo': 'Lista verificada'}},
                                           'added_rows': [], 'deleted_rows': []}
            self.boton('Usar Asistencia por Voz').click()
            self.boton('Confirmar y Aprobar').click().run()
            self.comprobar()
            guardar.assert_called_once()
            registro = guardar.call_args.args[0][1]
            self.assertEqual(registro['estado_deteccion'], 'SIN_MUESTRA')
            self.assertIsNone(registro['presente_detectado'])
            self.assertFalse(registro['presente'])

    def test_logout_estudiante_renueva_camara_y_borra_muestras(self):
        estado = {}
        iniciar_sesion('estudiante', {'estudiante_id': 7, 'nombre': 'Alumno'}, estado)
        token = estado['sesion_token']
        estado[f'auth_estudiante_camara_{token}'] = 'captura anterior'
        estado[f'auth_estudiante_voz_{token}'] = 'voz anterior'
        self.cargar(estado)
        self.at.run()
        self.at.button(key='loginbackbtn').click().run()
        self.comprobar()
        self.assertNotIn('datos_estudiante', self.at.session_state)
        self.assertNotIn(f'auth_estudiante_voz_{token}', self.at.session_state)
        self.assertNotEqual(token, self.at.session_state['sesion_token'])
        self.assertEqual(self.at.camera_input[0].key,
                         f"auth_estudiante_camara_{self.at.session_state['sesion_token']}")
        self.assertIsNone(self.at.camera_input[0].value)

    def test_qr_no_cierra_una_sesion_docente_ni_cambia_su_rol(self):
        self.profesor(pendiente=True)
        self.at.query_params['join-code'] = 'A'
        token=self.at.session_state['sesion_token']
        self.at.run()
        self.comprobar()
        self.assertEqual(self.at.session_state['tipo_sesion'], 'profesor')
        self.assertTrue(self.at.session_state['sesion_iniciada'])
        self.assertEqual(self.at.session_state['sesion_token'],token)
        self.assertIn('resultado_asistencia', self.at.session_state)

    def test_invitacion_bloquea_dialogo_manual_y_solo_limpia_su_parametro(self):
        estado = {}
        iniciar_sesion('estudiante', {'estudiante_id': 7, 'nombre': 'Alumno'}, estado)
        self.cargar(estado)
        self.at.query_params['join-code'] = 'A'
        self.at.query_params['otro'] = 'conservar'
        with patch('src.componentes.dialogo_inscripcion_automatica.obtener_materia_por_codigo', return_value={
                'materia_id': 10, 'nombre': 'Materia A'}), patch(
                'src.componentes.dialogo_inscripcion_automatica.esta_estudiante_matriculado', return_value=True):
            self.at.run()
            self.comprobar()
            self.assertTrue(self.boton('Inscribirse en una Materia').disabled)
            self.boton('¡Entendido!').click().run()
        self.comprobar()
        self.assertNotIn('join-code', self.at.query_params)
        self.assertEqual(self.at.query_params['otro'], 'conservar')
        self.assertFalse(self.boton('Inscribirse en una Materia').disabled)


if __name__ == '__main__':
    unittest.main()
