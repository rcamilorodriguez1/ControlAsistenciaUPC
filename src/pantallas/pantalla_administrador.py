"""Administración institucional: consulta, exportación y edición con trazabilidad."""
from datetime import datetime, time, timedelta
import logging
import streamlit as st

from src.base_datos import administracion as datos
from src.componentes.encabezado import encabezado_panel, introduccion
from src.componentes.pie_pagina import pie_pagina_panel
from src.componentes.seguridad_claves import mostrar_fortaleza
from src.utilidades.fecha_hora import hora_actual_colombia, ZONA_HORARIA_COLOMBIA
from src.utilidades.sesiones import iniciar_sesion, sesion_activa, cerrar_sesion
from src.servicios.sesiones_servidor import SesionInvalida
from src.utilidades.sesiones import sesion_incompatible
from src.componentes.conflicto_sesion import mostrar_conflicto_sesion

_logger = logging.getLogger(__name__)


def pantalla_administrador():
    if not sesion_activa('administrador'):
        _acceso(); return
    encabezado_panel('administrador', autenticado=True)
    introduccion('Administración institucional', 'Cuentas, materias y auditoría',
                 'Gestiona la información académica y consulta la trazabilidad de cada cambio.')
    modulo = st.radio('Módulo administrativo', ['Auditoría', 'Cuentas', 'Materias', 'Verificación'], horizontal=True, key='admin_modulo')
    try:
        if modulo == 'Auditoría': _auditoria()
        elif modulo == 'Cuentas': _cuentas()
        elif modulo == 'Materias': _materias()
        else:
            from src.componentes.gestion_excepciones import gestion_excepciones
            gestion_excepciones()
    except SesionInvalida:
        raise
    except PermissionError:
        cerrar_sesion('administrador')
        st.session_state['aviso_sesion'] = 'La cuenta administrativa no está activa. Inicia sesión de nuevo.'
        st.rerun()
    except ValueError as exc: st.warning(str(exc))
    except Exception as exc:
        _logger.error('Fallo administrativo: modulo=%s tipo=%s', modulo, type(exc).__name__)
        st.error('No se pudo completar la operación. Revisa el estado antes de repetir un cambio.')
    pie_pagina_panel()


def _acceso():
    conflicto = bool(sesion_incompatible('administrador'))
    encabezado_panel()
    token = st.session_state.sesion_token
    with st.container(key='acceso_administrativo'):
        st.caption('ADMINISTRACIÓN INSTITUCIONAL')
        st.header('Acceso administrativo')
        st.caption('Solo para cuentas habilitadas por el responsable del proyecto.')
        usuario = st.text_input('Usuario administrativo', max_chars=100, key=f'auth_administrador_usuario_{token}')
        clave = st.text_input('Contraseña', type='password', key=f'auth_administrador_clave_{token}')
        if st.button('Ingresar a Administración', disabled=conflicto, type='primary', width='stretch'):
            if not usuario or not clave:
                st.warning('Completa tu usuario y contraseña.'); return
            try: perfil = datos.autenticar(usuario, clave)
            except ValueError: perfil = None
            except Exception as exc:
                _logger.error('Fallo de acceso administrativo: tipo=%s', type(exc).__name__)
                st.error('No se pudo verificar el acceso. Intenta nuevamente.'); return
            if perfil:
                iniciar_sesion('administrador', perfil); st.rerun()
            else: st.error('Credenciales inválidas o acceso temporalmente bloqueado.')
    mostrar_conflicto_sesion('administrador')
    pie_pagina_panel()


def _auditoria():
    st.subheader('Historial de cambios')
    st.caption('Consulta y exportación. Los registros históricos no se editan ni se eliminan desde este panel.')
    hoy = hora_actual_colombia().date()
    with st.form('admin_filtro_auditoria'):
        tipos = {'Gestión de cuentas y materias': 'GESTION', 'Cambios de asistencia': 'ASISTENCIA', 'Matrículas y retiros': 'MATRICULAS'}
        categoria = st.selectbox('Historial', list(tipos))
        c1, c2 = st.columns(2)
        with c1: desde = st.date_input('Desde', value=hoy-timedelta(days=30))
        with c2: hasta = st.date_input('Hasta', value=hoy)
        limite = st.selectbox('Máximo de registros', [100, 500, 2000, 10000], index=1)
        buscar = st.form_submit_button('Consultar auditoría', type='primary')
    if buscar:
        if hasta < desde: raise ValueError('La fecha final debe ser igual o posterior a la inicial.')
        inicio = datetime.combine(desde, time.min, tzinfo=ZONA_HORARIA_COLOMBIA)
        final = datetime.combine(hasta+timedelta(days=1), time.min, tzinfo=ZONA_HORARIA_COLOMBIA)
        filas = datos.auditoria(tipos[categoria], inicio, final, limite)
        st.session_state['admin_resultado'] = {'tipo': tipos[categoria], 'filas': filas, 'limite': limite}
        st.session_state.pop('admin_csv', None)
    resultado = st.session_state.get('admin_resultado')
    if not resultado: return
    filas = resultado['filas']
    st.caption(f"{len(filas)} registros mostrados; límite de consulta y exportación: {resultado['limite']}. Acota el periodo si alcanzas el límite.")
    if not filas:
        st.info('No se encontraron cambios en el periodo seleccionado.'); return
    st.dataframe(filas, hide_index=True, width='stretch')
    if st.button('Generar CSV de estos resultados', key='admin_generar_csv'):
        st.session_state['admin_csv'] = datos.exportar_csv(resultado['tipo'], filas)
    if st.session_state.get('admin_csv'):
        st.download_button('Descargar CSV', st.session_state['admin_csv'],
            file_name='auditoria_' + resultado['tipo'].lower() + '.csv', mime='text/csv', key='admin_descargar_csv')


def _cuentas():
    st.subheader('Editar cuentas')
    tipo = st.selectbox('Tipo de cuenta', ['PROFESOR', 'ESTUDIANTE'], format_func=lambda t: 'Profesor' if t == 'PROFESOR' else 'Estudiante')
    busqueda = st.text_input('Buscar por nombre, usuario o últimos cuatro caracteres del documento', max_chars=100, key='admin_buscar_cuenta')
    filas = datos.cuentas(tipo, busqueda)
    st.caption('Hasta 500 coincidencias. Usa la búsqueda para localizar una cuenta concreta.')
    if not filas:
        st.info('No hay cuentas que coincidan con la búsqueda.'); return
    por_id = {f['id']: f for f in filas}
    identidad = st.selectbox('Cuenta', list(por_id), format_func=lambda i: f"#{i} · {por_id[i]['nombre']} · {'Activa' if por_id[i]['activo'] else 'Archivada'}", key=f'admin_cuenta_{tipo}')
    base = f'admin_base_cuenta_{tipo}_{identidad}'
    if st.button('Recargar datos de la cuenta'):
        st.session_state.pop(base, None); st.rerun()
    fila = st.session_state.setdefault(base, dict(por_id[identidad]))
    version = fila['version']
    prefijo = f'admin_editar_{tipo}_{identidad}_{version}'
    nombre = st.text_input('Nombre completo', value=fila['nombre'], max_chars=200, key=prefijo+'_nombre')
    identificador = st.text_input('Usuario', value=fila.get('usuario') or '',max_chars=100,
                                  key=prefijo+'_identificador') if tipo=='PROFESOR' else fila.get('codigo_institucional') or ''
    activo = st.checkbox('Cuenta activa', value=bool(fila['activo']), key=prefijo+'_activo')
    nueva_clave = ''
    cambiar_clave = False
    if tipo == 'PROFESOR':
        cambiar_clave = st.checkbox('Establecer una nueva contraseña', key=prefijo+'_cambiar_clave')
        if cambiar_clave:
            nueva_clave = st.text_input('Nueva contraseña', type='password', live='300ms', autocomplete='new-password', key=prefijo+'_clave')
            mostrar_fortaleza(nueva_clave, usuario=identificador, nombre=nombre)
    else:
        st.caption('Archivar al estudiante retira sus matrículas y elimina su biometría activa; conserva el historial. Reactivarlo no recupera los vectores eliminados.')
    motivo = st.text_input('Motivo del cambio', max_chars=500, key=prefijo+'_motivo')
    confirmar = st.checkbox('He revisado los cambios de esta cuenta', key=prefijo+'_confirmar')
    if st.button('Guardar cambios de cuenta', type='primary', disabled=not confirmar):
        if cambiar_clave and not nueva_clave: raise ValueError('Escribe la nueva contraseña o desmarca el cambio de contraseña.')
        if tipo == 'PROFESOR': datos.editar_profesor(identidad, identificador, nombre, activo, motivo, nueva_clave, version=version)
        else: datos.editar_estudiante(identidad, identificador, nombre, activo, motivo, version=version)
        st.session_state.pop(base, None)
        st.toast('Cambios guardados y registrados en auditoría.'); st.rerun()
    if tipo == 'ESTUDIANTE':
        from src.servicios import documentos_estudiantes as documentos
        from src.servicios.verificacion_identidad import TIPOS_DOCUMENTO
        st.caption(documentos.etiqueta_documento(fila.get('tipo_documento'),fila.get('documento_final')))
        with st.form(f'admin_documento_{identidad}_{fila.get("version_documento",0)}',clear_on_submit=True):
            tipo_doc=st.selectbox('Tipo de documento del estudiante',TIPOS_DOCUMENTO)
            numero_doc=st.text_input('Número del documento del estudiante',max_chars=40)
            comprobado=st.checkbox('Comprobé que el documento corresponde a este estudiante.')
            st.caption('Actualizar el documento cierra las sesiones y revoca la contraseña excepcional anterior.')
            guardar_doc=st.form_submit_button('Guardar documento del estudiante',disabled=not bool(fila['activo']))
        if guardar_doc:
            documentos.guardar_administrativo(identidad,tipo_doc,numero_doc,
                version=int(fila.get('version_documento',0)),comprobado=comprobado)
            st.session_state.pop(base,None)
            st.toast('Documento guardado; el estudiante debe iniciar sesión nuevamente.');st.rerun()


def _materias():
    st.subheader('Editar materias')
    busqueda = st.text_input('Buscar materia por nombre o código', max_chars=100, key='admin_buscar_materia')
    filas = datos.materias(busqueda)
    st.caption('Hasta 500 coincidencias. El archivo conserva las clases y asistencias existentes.')
    if not filas:
        st.info('No hay materias que coincidan con la búsqueda.'); return
    por_id = {f['id']: f for f in filas}
    identidad = st.selectbox('Materia', list(por_id), format_func=lambda i: f"{por_id[i]['codigo_materia']} · {por_id[i]['nombre']}", key='admin_materia')
    base = f'admin_base_materia_{identidad}'
    if st.button('Recargar datos de la materia'):
        st.session_state.pop(base, None); st.rerun()
    fila = st.session_state.setdefault(base, dict(por_id[identidad]))
    version = fila['version']; prefijo = f'admin_materia_{identidad}_{version}'
    codigo = st.text_input('Código de materia', value=fila['codigo_materia'], max_chars=50, key=prefijo+'_codigo')
    nombre = st.text_input('Nombre de materia', value=fila['nombre'], max_chars=200, key=prefijo+'_nombre')
    seccion = st.text_input('Sección', value=fila.get('seccion') or '', max_chars=100, key=prefijo+'_seccion')
    profesores = {p['id']: p for p in datos.cuentas('PROFESOR')}
    if fila['profesor_id'] not in profesores: raise ValueError('Busca el docente de esta materia antes de reasignarla; no aparece entre las primeras 500 cuentas.')
    ids = list(profesores)
    profesor = st.selectbox('Profesor responsable', ids, index=ids.index(fila['profesor_id']),
        format_func=lambda i: f"#{i} · {profesores[i]['nombre']}", disabled=fila['clases']>0, key=prefijo+'_profesor')
    if fila['clases']>0: st.caption('Las materias con clases conservan su docente para proteger la autoría histórica.')
    activo = st.checkbox('Materia activa', value=bool(fila['activo']), key=prefijo+'_activo')
    motivo = st.text_input('Motivo del cambio de materia', max_chars=500, key=prefijo+'_motivo')
    confirmar = st.checkbox('He revisado los cambios de esta materia', key=prefijo+'_confirmar')
    if st.button('Guardar cambios de materia', type='primary', disabled=not confirmar):
        datos.editar_materia(identidad, codigo, nombre, seccion, profesor, activo, motivo, version=version)
        st.session_state.pop(base, None)
        st.toast('Materia actualizada y cambio auditado.'); st.rerun()
