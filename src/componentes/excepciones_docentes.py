"""El docente comprueba la identidad y entrega manualmente la contraseña alternativa."""
import streamlit as st
from uuid import uuid4
from src.base_datos.bd import obtener_materias_profesor
from src.servicios import excepciones_docentes as servicio
from src.servicios.verificacion_identidad import CATEGORIAS
from src.utilidades.sesiones import obtener_actor


def gestionar_excepciones_docentes():
    actor = obtener_actor(renovar=True)
    if actor is None or actor[0] != 'profesor':
        raise PermissionError('Se requiere una sesión docente.')
    st.header('Excepciones de acceso')
    st.caption('Autoriza a un estudiante de tus materias cuando no pueda iniciar con su rostro. '
        'Entrega la clave personalmente al estudiante; no se envían correos.')
    if aviso := st.session_state.pop('aviso_excepcion_docente', None):
        st.success(aviso)
    materias = {m['materia_id']: m for m in obtener_materias_profesor(actor[1])}
    if not materias:
        st.info('Necesitas una materia activa con estudiantes matriculados.')
        return
    mid = st.selectbox('Materia de la solicitud', list(materias), key=f'excepcion_materia_{actor[2]}',
        format_func=lambda i: materias[i]['nombre']+' · '+materias[i]['codigo_materia'])
    try:
        filas = servicio.listar(mid)
    except (ValueError, PermissionError) as exc:
        st.warning(str(exc))
        return
    alumnos = {int(f['estudiante_id']): f for f in filas}
    if not alumnos:
        st.info('Esta materia no tiene estudiantes activos matriculados.')
        return
    sid = st.selectbox('Estudiante que solicita la excepción', list(alumnos),
        key=f'excepcion_estudiante_{actor[2]}_{mid}',
        format_func=lambda i: alumnos[i]['nombre']+' · '+str(alumnos[i]['codigo_institucional'] or 'Sin código'))
    alumno = alumnos[sid]
    generacion = st.session_state.get('excepcion_docente_formulario', '')
    prefijo = f'excepcion_docente_{actor[2]}_{mid}_{sid}_{alumno["version_credencial"]}_{generacion}'
    st.info('Esta clave permite iniciar sesión en la cuenta del estudiante durante la vigencia autorizada. '
        'La asistencia de las clases se confirma por separado.')
    if alumno['excepcion_vigente']:
        st.caption(f"Excepción vigente hasta {alumno['expira_en']}.")
    if alumno['puede_autorizar']:
        with st.form(prefijo, clear_on_submit=True):
            tipo = st.selectbox('Tipo de documento', ['CC', 'TI', 'CE', 'PA'])
            documento = st.text_input('Número de documento', type='password', max_chars=40, key=prefijo+'_documento')
            categoria = st.selectbox('Motivo de la excepción', list(CATEGORIAS), format_func=lambda c: c.capitalize())
            referencia = st.text_input('Referencia de autorización', max_chars=100,
                help='Una referencia breve para identificar la solicitud; no incluyas diagnósticos médicos.')
            dias = st.number_input('Vigencia en días', min_value=1, max_value=365, value=1, step=1)
            clave = st.text_input('Clave para entregar al estudiante', type='password', autocomplete='new-password', key=prefijo+'_clave')
            confirmar = st.text_input('Confirmar clave', type='password', autocomplete='new-password', key=prefijo+'_confirmar')
            comprobado = st.checkbox('Comprobé el documento y la identidad del estudiante')
            enviar = st.form_submit_button('Autorizar y entregar clave', type='primary')
        if enviar:
            try:
                if clave != confirmar:
                    raise ValueError('Las contraseñas no coinciden.')
                servicio.autorizar(mid, sid, tipo, documento, clave, categoria, referencia, int(dias),
                    version=int(alumno['version_credencial']), documento_comprobado=comprobado)
            except (ValueError, PermissionError) as exc:
                st.warning(str(exc))
            else:
                for campo in ('documento', 'clave', 'confirmar'):
                    st.session_state.pop(prefijo+'_'+campo, None)
                st.session_state['excepcion_docente_formulario'] = uuid4().hex
                st.session_state['aviso_excepcion_docente'] = 'Autorización guardada. Entrega la clave acordada al estudiante; podrá usar Acceso por excepción con su documento.'
                st.rerun()
    else:
        st.warning('Esta autorización pertenece a Administración u otro docente. Solicita revisión administrativa para cambiarla.')
    if alumno['puede_revocar']:
        with st.form(prefijo+'_revocar', clear_on_submit=True):
            motivo = st.text_input('Motivo de revocación', max_chars=450)
            confirmar_revocacion = st.checkbox('Confirmo que quiero revocar esta excepción')
            revocar = st.form_submit_button('Revocar excepción')
        if revocar:
            try:
                if not confirmar_revocacion:
                    raise ValueError('Confirma la revocación.')
                servicio.revocar(mid, sid, motivo, version=int(alumno['version_credencial']))
            except (ValueError, PermissionError) as exc:
                st.warning(str(exc))
            else:
                st.session_state['aviso_excepcion_docente'] = 'Excepción revocada. La clave y las sesiones anteriores dejan de ser válidas.'
                st.rerun()
