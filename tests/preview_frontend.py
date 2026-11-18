"""Vista aislada con datos sintéticos. Toda conexión Oracle queda bloqueada.

Ejecutar únicamente con scripts/verificar_frontend.py --paneles.
No añade accesos ni rutas de prueba a principal.py.
"""
from contextlib import ExitStack
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from soporte_perfil import filas_perfil
import streamlit as st
from src.interfaz.diseno_base import estilo_diseno_base, RAIZ
from src.utilidades.sesiones import iniciar_sesion, preparar_toma, guardar_resultado, cerrar_sesion, inicializar_sesion
from src.pantallas.pantalla_profesor import pantalla_profesor
from src.pantallas.pantalla_estudiante import pantalla_estudiante

st.set_page_config(page_title='Vista de prueba · UPC | Aula', layout='wide', page_icon=str(RAIZ / 'static/img/upc/logo-vertical-manual.jpg'))
estilo_diseno_base()


@st.cache_resource
def aislar_repositorios():
    """También protege los callbacks, ejecutados ANTES de evaluar este script en cada rerun."""
    from secrets import token_urlsafe
    bloquear = AssertionError('La vista de prueba no permite conexiones a Oracle.')
    parches = [
        patch('src.base_datos.configuracion.obtener_pool', side_effect=bloquear),
        patch('src.base_datos.bd.obtener_conexion', side_effect=bloquear),
        patch('src.servicios.sesiones_servidor.abrir', side_effect=lambda *a, **kw: token_urlsafe(32)),
        patch('src.pantallas.pantalla_estudiante.acreditar_biometria', side_effect=lambda p:p),
        patch('src.pantallas.pantalla_estudiante.registrar_fallo_biometrico'),
        patch('src.servicios.sesiones_servidor.validar', return_value=None),
        patch('src.servicios.sesiones_servidor.cerrar', return_value=None),
    ]
    for parche in parches:
        parche.start()
    return parches  # Viven solo durante el proceso separado de esta vista sintética.


aislar_repositorios()
inicializar_sesion()
def renderizar_vista():
    rol = st.session_state.get('tipo_sesion')
    if rol is None:
        from src.pantallas.pantalla_inicio import pantalla_inicio
        pantalla_inicio()
        return
    materias = [
        {'materia_id': 10, 'codigo_materia': 'BD-301', 'nombre': 'Bases de Datos', 'seccion': 'Grupo 01', 'profesor_id': 990001, 'total_estudiantes': 23, 'total_clases': 4},
        {'materia_id': 20, 'codigo_materia': 'IS-402', 'nombre': 'Ingeniería de Software', 'seccion': 'Grupo 02', 'profesor_id': 990001, 'total_estudiantes': 18, 'total_clases': 6}]
    registros = [{'clase_id': 100 + i, 'materia_id': 10, 'fecha_hora': f'2026-11-0{8+i}T08:15:00.000000-05:00',
        'fecha_clase': f'2026-11-0{8+i}T08:00:00.000000-05:00', 'materia': materias[0], 'presente': True,
        'corregido_manual': False, 'origen': 'FACIAL'} for i in range(2)]
    estudiantes = [{'estudiante_id': 990007, 'nombre': 'Estudiante de prueba A', 'embedding_facial': [.1] * 128, 'embedding_voz': None},
                   {'estudiante_id': 990008, 'nombre': 'Estudiante de prueba B', 'embedding_facial': None, 'embedding_voz': None}]

    with ExitStack() as parches:
        bloquear = AssertionError('La vista de prueba no permite conexiones a Oracle.')
        # Bloqueo del proveedor global: cubre también funciones importadas antes del parche.
        parches.enter_context(patch('src.base_datos.configuracion.obtener_pool', side_effect=bloquear))
        parches.enter_context(patch('src.base_datos.bd.obtener_conexion', side_effect=bloquear))
        if rol == 'estudiante' and st.query_params.get('registro') == '1':
            from io import BytesIO
            from PIL import Image
            if not st.session_state.get('sesion_token') or st.session_state.get('sesion_iniciada'):
                paginas = {k: st.session_state[k] for k in ('_pagina_inicio', '_paginas_portal', '_pagina_perfil_estudiante') if k in st.session_state}
                cerrar_sesion('estudiante')
                st.session_state.update(paginas)
            st.session_state['mostrar_registro_estudiante'] = True
            def captura_sintetica(*args, **kwargs):
                archivo = BytesIO()
                Image.new('RGB', (256, 256), '#dddddd').save(archivo, format='JPEG')
                archivo.seek(0)
                return archivo
            parches.enter_context(patch('src.pantallas.pantalla_estudiante.st.camera_input', side_effect=captura_sintetica))
            st.caption('REGISTRO DE PRUEBA · CAPTURA SINTÉTICA · ORACLE BLOQUEADO')
            pantalla_estudiante()
            return
        lecturas = {
            'src.pantallas.pantalla_profesor.obtener_resumen_profesor': {'total_materias': 2, 'total_estudiantes': 41, 'asistencia_promedio': 91},
            'src.pantallas.pantalla_profesor.obtener_materias_profesor': materias,
            'src.componentes.gestion_cuenta.obtener_materias_profesor': materias,
            'src.pantallas.pantalla_profesor.obtener_asistencia_profesor': registros,
            'src.pantallas.pantalla_profesor.obtener_estudiantes_matriculados': estudiantes,
            'src.pantallas.pantalla_estudiante.obtener_resumen_estudiante': {'total_materias': 2, 'total_clases': 6, 'asistencia_promedio': 83},
            'src.pantallas.pantalla_estudiante.obtener_materias_estudiante': [{'materia': m} for m in materias],
            'src.pantallas.pantalla_estudiante.obtener_asistencia_estudiante': registros,
            'src.servicios.perfil_estudiante.consultar_datos': (
                [{'estudiante_id': 990007, 'nombre_estudiante': 'Estudiante de prueba',
                  'codigo_institucional': None, 'materia_id': None, 'clase_id': None}]
                if st.query_params.get('perfil-vacio') == '1' else filas_perfil()),
            'src.componentes.dialogo_asistencia_voz.obtener_estudiantes_matriculados': estudiantes}
        for destino, valor in lecturas.items(): parches.enter_context(patch(destino, return_value=valor))
        parches.enter_context(patch('src.componentes.selector_clase.obtener_clases_profesor', side_effect=lambda m, p: [
            {'clase_id': 100 if m == 10 else 200, 'materia_id': m, 'estado': 'BORRADOR', 'origen': 'PENDIENTE',
             'lote_legado': 0, 'fecha_hora': '2026-11-11T08:00:00.000000-05:00'}]))
        if rol == 'administrador':
            parches.enter_context(patch('src.servicios.excepciones_biometricas.listar', return_value=[dict(
                estudiante_id=990007,nombre='Estudiante de prueba',codigo_institucional='PREVIEW-7',activo=1,
                estado_verificacion='EXCEPCIONAL',excepcion_activa=1,excepcion_vigente=1,
                tipo_documento='CC',documento='****0000',categoria='TECNICA',referencia='EXP-SINTETICO',
                version_credencial=3,factores_verificados=0,factores_requeridos=1,tiene_rostro=0,tiene_voz=0)]))
            for metodo in ('autorizar','revocar'):
                parches.enter_context(patch('src.servicios.excepciones_biometricas.'+metodo, side_effect=bloquear))
        fixture = st.query_params.get('fixture')
        if fixture in ('profesor', 'estudiante', 'administrador'):
            del st.query_params['fixture']
            pagina_inicio=st.session_state.get('_pagina_inicio')
            paginas_portal=st.session_state.get('_paginas_portal')
            pagina_perfil=st.session_state.get('_pagina_perfil_estudiante')
            vista_estudiante=st.session_state.get('_vista_estudiante', 'portal')
            cerrar_sesion()
            perfil = {'nombre': 'Estudiante de prueba', 'estudiante_id': 990007} if fixture == 'estudiante' else {
                'nombre': 'Cuenta de prueba', fixture+'_id': 990001, 'usuario': 'preview'}
            iniciar_sesion(fixture, perfil)
            if fixture == 'estudiante' and st.query_params.get('excepcion') == '1':
                st.session_state['datos_estudiante']['estado_verificacion'] = 'EXCEPCIONAL'
            st.session_state['_pagina_inicio']=pagina_inicio
            st.session_state['_paginas_portal']=paginas_portal
            st.session_state['_pagina_perfil_estudiante']=pagina_perfil
            st.session_state['_vista_estudiante']=vista_estudiante
            st.session_state['tipo_sesion']=rol
            if fixture == 'estudiante':
                from datetime import date
                st.session_state['perfil_mes'] = date(2026, 11, 1)
            if fixture == 'profesor':
                st.session_state['clase_por_seleccionar'] = {'materia_id': 10, 'clase_id': 100}
                contexto = preparar_toma(10, clase_id=100)
                guardar_resultado(contexto, [{'Nombre': e['nombre'], 'ID': e['estudiante_id'], 'Estado': 'Presente' if i == 0 else 'Sin muestra'} for i, e in enumerate(estudiantes)],
                    [{'materia_id': 10, 'estudiante_id': e['estudiante_id'], 'fecha_hora': '2026-11-11T08:15:00-05:00',
                      'presente': True if i == 0 else None, 'estado_deteccion': 'PRESENTE' if i == 0 else 'SIN_MUESTRA'} for i, e in enumerate(estudiantes)], 'facial')
        st.caption('VISTA DE PRUEBA · DATOS SINTÉTICOS · ORACLE BLOQUEADO')
        if rol == 'profesor': pantalla_profesor()
        elif rol == 'administrador':
            from src.pantallas.pantalla_administrador import pantalla_administrador
            pantalla_administrador()
        elif st.session_state.get('_vista_estudiante') == 'perfil':
            from src.pantallas.perfil_estudiante import pantalla_perfil_estudiante
            pantalla_perfil_estudiante()
        else: pantalla_estudiante()


from src.interfaz.navegacion import navegar
navegar(renderizar_vista)
