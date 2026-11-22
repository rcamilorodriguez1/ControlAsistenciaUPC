import unittest
from unittest.mock import patch,MagicMock
from pathlib import Path
from streamlit.testing.v1 import AppTest
from soporte_sesiones import simular_sesiones
from src.utilidades.sesiones import iniciar_sesion,preparar_toma
from src.servicios.sesiones_servidor import SesionInvalida


class NavegacionGlobalTest(unittest.TestCase):
    def setUp(self):
        from src.servicios.sesiones_servidor import abrir
        self.abrir_real = abrir
        simular_sesiones(self)
        lecturas={
            'src.pantallas.pantalla_profesor.obtener_resumen_profesor':{'total_materias':1,'total_estudiantes':1,'asistencia_promedio':0},
            'src.pantallas.pantalla_profesor.obtener_materias_profesor':[{'materia_id':10,'codigo_materia':'TEST','nombre':'Materia','seccion':'A','profesor_id':1,'total_estudiantes':1,'total_clases':1}],
            'src.componentes.selector_clase.obtener_clases_profesor':[{'clase_id':100,'materia_id':10,'estado':'BORRADOR','origen':'PENDIENTE','lote_legado':0,'fecha_hora':'2026-11-11T08:00:00-05:00'}],
            'src.componentes.gestion_cuenta.obtener_materias_profesor':[],
            'src.pantallas.pantalla_estudiante.obtener_resumen_estudiante':{'total_materias':0,'total_clases':0,'asistencia_promedio':0},
            'src.pantallas.pantalla_estudiante.obtener_materias_estudiante':[],
            'src.pantallas.pantalla_estudiante.obtener_asistencia_estudiante':[],
            'src.base_datos.administracion.cuentas':[],
        }
        for n,v in lecturas.items():
            p=patch(n,return_value=v);p.start();self.addCleanup(p.stop)

    def crear(self,rol):
        perfil={rol+'_id':1,'nombre':'Perfil de prueba','usuario':'fixture'}
        estado={};iniciar_sesion(rol,perfil,estado)
        if rol=='profesor':
            preparar_toma(10,estado,clase_id=100)
            estado['pestana_actual_profesor']='gestionar_materias'
        if rol=='administrador':estado['admin_modulo']='Cuentas'
        estado['borrador_navegacion']='se conserva'
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'principal.py'),default_timeout=35)
        for k,v in estado.items():at.session_state[k]=v
        from streamlit.util import calc_hash
        at._page_hash=calc_hash({'profesor':'docente','estudiante':'estudiante','administrador':'administracion'}[rol])
        at.run();self.assertFalse(at.exception)
        return at,estado['sesion_token']

    def test_inicio_nativo_conserva_sesion_y_rol_en_los_tres_portales(self):
        for rol in ('profesor','estudiante','administrador'):
            with self.subTest(rol=rol):
                at,token=self.crear(rol)
                # AppTest no ofrece click/switch_page para paginas callable: se envia su hash registrado,
                # igual que el enlace nativo; no se construye una sesion ni un router alternativo.
                pagina=at.session_state['_pagina_inicio']
                at._page_hash=pagina._script_hash
                at.run();self.assertFalse(at.exception)
                self.assertEqual(at.session_state['sesion_token'],token)
                self.assertEqual(at.session_state['rol_usuario'],rol)
                self.assertTrue(at.session_state['sesion_iniciada'])
                self.assertEqual(at.session_state['borrador_navegacion'],'se conserva')
                self.assertIsNone(at.session_state['tipo_sesion'])
                self.assertTrue(any(b.label == 'Portal del Profesor' for b in at.button))
                at._page_hash=at.session_state['_paginas_portal'][rol]._script_hash
                at.run();self.assertFalse(at.exception)
                self.assertEqual(at.session_state['sesion_token'],token)
                if rol=='profesor':self.assertEqual(at.session_state['pestana_actual_profesor'],'gestionar_materias')
                if rol=='administrador':self.assertEqual(at.session_state['admin_modulo'],'Cuentas')

    def test_sesion_reemplazada_no_muestra_panel_y_explica_el_motivo(self):
        for rol in ('profesor','estudiante','administrador'):
            at,token=self.crear(rol)
            with patch('src.servicios.sesiones_servidor.validar',side_effect=SesionInvalida('Tu sesión fue reemplazada por otro acceso.')):
                at.run()
            self.assertFalse(at.exception)
            self.assertFalse(at.session_state['sesion_iniciada'])
            self.assertNotIn('datos_'+rol,at.session_state)
            self.assertTrue(any('reemplazada' in w.value for w in at.warning))

    def test_cierre_revoca_el_token_de_cada_rol(self):
        for rol in ('profesor','estudiante','administrador'):
            at,token=self.crear(rol)
            with patch('src.servicios.sesiones_servidor.cerrar') as revocar:
                at.button(key='loginbackbtn').click().run()
                revocar.assert_called_once_with(rol,1,token)
            self.assertFalse(at.exception)
            self.assertFalse(at.session_state['sesion_iniciada'])
            self.assertNotIn('datos_'+rol,at.session_state)

    def test_no_reautentica_ni_cambia_a_otro_rol_si_ya_tiene_sesion_valida(self):
        for rol in ('profesor','estudiante','administrador'):
            estado={};iniciar_sesion(rol,{rol+'_id':1,'nombre':'Perfil','usuario':'fixture'},estado)
            token=estado['sesion_token']
            with patch('streamlit.session_state',estado),patch('src.servicios.sesiones_servidor.abrir') as abrir:
                from src.servicios.autenticacion import ConflictoSesion
                with self.assertRaises(ConflictoSesion):
                    iniciar_sesion('profesor',{'profesor_id':999,'nombre':'Otro','usuario':'otro'})
                abrir.assert_not_called()
            self.assertEqual(estado['sesion_token'],token)
            self.assertEqual(estado['rol_usuario'],rol)

    def test_backend_rechaza_token_revocado_antes_de_la_operacion(self):
        from src.base_datos import bd
        conn=MagicMock();operacion=MagicMock()
        with patch.object(bd,'obtener_conexion',return_value=conn),patch.object(bd,'obtener_pool'),patch.object(bd,'_contexto_auditoria_actual',return_value=('PROFESOR',1,None)),patch('src.utilidades.sesiones._actor_local',return_value=('profesor',1,'token-fixture-seguro')),patch('src.servicios.sesiones_servidor.validar_en_conexion',side_effect=SesionInvalida('Reemplazada')):
            with self.assertRaises(SesionInvalida):bd.ejecutar_con_reintentos(operacion)
        operacion.assert_not_called()

    def test_conflicto_en_todas_las_combinaciones_no_sustituye_el_login(self):
        roles = ('profesor', 'estudiante', 'administrador')
        for actual in roles:
            for solicitado in roles:
                if actual == solicitado:
                    continue
                with self.subTest(actual=actual, solicitado=solicitado):
                    at, token = self.crear(actual)
                    at._page_hash=at.session_state['_paginas_portal'][solicitado]._script_hash
                    at.run(); self.assertFalse(at.exception)
                    self.assertTrue(any(h.value == 'Ya tienes una sesión activa' for h in at.subheader))
                    if solicitado == 'estudiante':
                        self.assertTrue(at.camera_input[0].disabled)
                    else:
                        etiqueta = 'Iniciar Sesión' if solicitado == 'profesor' else 'Ingresar a Administración'
                        self.assertTrue(next(b for b in at.button if b.label == etiqueta).disabled)
                        self.assertEqual(len(at.text_input), 2)
                    self.assertEqual(at.session_state['rol_usuario'], actual)
                    self.assertEqual(at.session_state['sesion_token'], token)
                    next(b for b in at.button if b.label == 'Volver a mi portal').click().run()
                    self.assertFalse(at.exception)
                    self.assertEqual(at.session_state['tipo_sesion'], actual)
                    self.assertEqual(at.session_state['sesion_token'], token)
                    at._page_hash=at.session_state['_paginas_portal'][solicitado]._script_hash
                    at.run()
                    with patch('src.servicios.sesiones_servidor.cerrar') as revocar:
                        next(b for b in at.button if b.label == 'Cerrar sesión actual').click().run()
                        revocar.assert_called_once_with(actual, 1, token)
                    self.assertFalse(at.exception)
                    self.assertEqual(at.session_state['tipo_sesion'], solicitado)
                    self.assertFalse(at.session_state['sesion_iniciada'])
                    self.assertFalse(any(h.value == 'Ya tienes una sesión activa' for h in at.subheader))
                    if solicitado == 'estudiante': self.assertFalse(at.camera_input[0].disabled)
                    else: self.assertFalse(next(b for b in at.button if b.label == etiqueta).disabled)

    def test_menu_docente_habilita_perfil_y_configuracion_sin_duplicar_inicio(self):
        at, _ = self.crear('profesor')
        menu = at.get('popover')[0]
        self.assertEqual([b.label for b in menu.button], ['Mi perfil', 'Configuración', 'Cerrar sesión'])
        self.assertFalse(menu.button[0].disabled)
        self.assertFalse(menu.button[1].disabled)

    def test_servicios_rechazan_login_alta_y_apertura_con_actor_vigente(self):
        from src.servicios import sesiones_servidor, registro_estudiante
        from src.base_datos import bd, administracion
        from src.servicios.autenticacion import ConflictoSesion
        acciones = [lambda: bd.iniciar_sesion_profesor('otro', 'clave'),
                    lambda: bd.crear_profesor('otro', 'clave', 'Otro'),
                    lambda: administracion.autenticar('otro', 'clave'),
                    lambda: registro_estudiante.registrar_estudiante('Otro', None),
                    lambda: self.abrir_real('estudiante', 9)]
        with patch('src.servicios.autenticacion.get_script_run_ctx', return_value=object()), \
             patch('src.utilidades.sesiones.obtener_actor', return_value=('profesor', 1, 'token-fixture')):
            for accion in acciones:
                with self.assertRaises(ConflictoSesion): accion()
