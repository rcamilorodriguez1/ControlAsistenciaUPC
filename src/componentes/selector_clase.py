from datetime import datetime, time

import streamlit as st

from src.base_datos.clases import abrir_clase, obtener_clases_profesor
from src.utilidades.fecha_hora import convertir_a_hora_colombia, hora_actual_colombia, ZONA_HORARIA_COLOMBIA


def selector_clase(materia_id, profesor_id):
    clases = obtener_clases_profesor(materia_id, profesor_id)
    por_id = {c['clase_id']: c for c in clases}
    clave = f'clase_selector_{profesor_id}_{materia_id}'
    pendiente = st.session_state.get('clase_por_seleccionar')
    if pendiente and pendiente['materia_id'] == materia_id and pendiente.get('profesor_id', profesor_id) == profesor_id:
        st.session_state[clave] = pendiente['clase_id'] if pendiente['clase_id'] in por_id else None
        del st.session_state['clase_por_seleccionar']
    if clave not in st.session_state:
        contexto = st.session_state.get('contexto_asistencia', {})
        actual = contexto.get('clase_id') if contexto.get('materia_id') == materia_id else None
        st.session_state[clave] = actual if actual in por_id else None
    if st.session_state[clave] not in por_id:
        st.session_state[clave] = None

    def etiqueta(clase_id):
        if clase_id is None:
            return 'Selecciona una clase'
        clase = por_id[clase_id]
        fecha = convertir_a_hora_colombia(clase['fecha_hora']).strftime('%d/%m/%Y %H:%M')
        estado = 'Confirmada' if clase['estado'] == 'CONFIRMADA' else 'Pendiente'
        legado = f" · lote histórico {clase['lote_legado']}" if clase.get('lote_legado') else ''
        return f'{fecha} · {estado}{legado}'

    with st.container(key='selector_academico_clase'):
        seleccionado = st.selectbox('Clase de esta materia', options=[None, *por_id],
                                    format_func=etiqueta, key=clave, placeholder='Selecciona una clase')
    with st.expander('Crear o abrir una clase'):
        st.caption('Usa la fecha y hora de inicio de la clase. Si ya existe ese horario, se abrirá la misma clase.')
        ahora = hora_actual_colombia()
        c1, c2 = st.columns(2)
        with c1:
            fecha = st.date_input('Fecha de la clase', value=ahora.date(), key=f'clase_fecha_{materia_id}')
        with c2:
            hora = st.time_input('Hora de inicio (Colombia)', value=time(ahora.hour), step=60,
                                 key=f'clase_hora_{materia_id}')
        if st.button('Crear o abrir este horario', key=f'clase_abrir_{materia_id}', type='primary'):
            try:
                clase_id = abrir_clase(materia_id, profesor_id, datetime.combine(fecha, hora, tzinfo=ZONA_HORARIA_COLOMBIA))
            except (ValueError, PermissionError) as exc:
                st.warning(str(exc))
            else:
                st.session_state['clase_por_seleccionar'] = {'materia_id': materia_id, 'profesor_id': profesor_id, 'clase_id': clase_id}
                st.rerun()
    return por_id.get(seleccionado)
