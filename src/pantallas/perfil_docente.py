"""Identidad docente y calendario; las operaciones se realizan desde el portal."""
import calendar
from datetime import date
from html import escape
import streamlit as st
from src.componentes.encabezado import encabezado_panel, introduccion
from src.servicios.perfil_docente import cargar_perfil_docente
from src.utilidades.fecha_hora import hora_actual_colombia
from src.utilidades.sesiones import sesion_activa, seleccionar_portal
from src.pantallas.perfil_estudiante import MESES, DIAS, _iniciales


def html_calendario_docente(mes, dias, hoy=None):
    hoy = hoy or hora_actual_colombia().date()
    filas = []
    for semana in calendar.Calendar().monthdayscalendar(mes.year, mes.month):
        celdas = []
        for n in semana:
            if not n:
                celdas.append('<td aria-hidden="true"></td>')
                continue
            dia = date(mes.year, mes.month, n)
            clases = dias.get(dia, [])
            detalle = '; '.join(c['fecha'].strftime('%H:%M') + ' ' + c['materia'] for c in clases)
            titulo = f'{dia.strftime("%d/%m/%Y")}: {detalle or "Sin clases programadas"}'
            actual = ' aria-current="date"' if dia == hoy else ''
            celdas.append(f'<td class="agenda-dia {"agenda-dia-con-clase" if clases else ""}" '
                f'title="{escape(titulo, quote=True)}"{actual}><strong>{n}</strong>'
                f'<span>{str(len(clases)) + " clases" if clases else "—"}</span></td>')
        filas.append('<tr>' + ''.join(celdas) + '</tr>')
    return ('<table class="agenda-calendario" aria-label="Agenda docente de ' + MESES[mes.month-1] +
        f' {mes.year}"><thead><tr>' + ''.join(f'<th scope="col">{d}</th>' for d in DIAS) +
        '</tr></thead><tbody>' + ''.join(filas) + '</tbody></table>')


def cambiar_mes_docente(delta):
    mes = st.session_state.get('docente_mes', hora_actual_colombia().date().replace(day=1))
    indice = (mes.year-1)*12 + mes.month-1 + delta
    if 0 <= indice < 9999*12:
        anio, numero = divmod(indice, 12)
        st.session_state['docente_mes'] = date(anio+1, numero+1, 1)
        st.session_state.pop('docente_dia', None)


def _lista_clases(clases):
    if not clases:
        st.caption('No hay clases en esta selección.')
        return
    st.html('<ul class="agenda-sesiones">' + ''.join(
        '<li><time>' + c['fecha'].strftime('%d/%m · %H:%M') + '</time><strong>' +
        escape(c['materia']) + '</strong><span>' +
        ('Confirmada' if c['estado'] == 'CONFIRMADA' else 'Programada' if c['fecha'] >= hora_actual_colombia() else 'Pendiente de confirmar') +
        (' · Materia archivada' if not c['activa'] else '') + '</span></li>' for c in clases) + '</ul>')


def pantalla_perfil_docente():
    if not sesion_activa('profesor'):
        raise PermissionError('El perfil requiere una sesión docente.')
    encabezado_panel('profesor', autenticado=True)
    st.button('Volver a mi portal', key='docente_volver_portal', type='tertiary',
        icon=':material/arrow_back:', on_click=seleccionar_portal, args=('profesor',))
    perfil = cargar_perfil_docente()
    with st.container(key='perfil_docente'):
        st.html('<section class="docente-portada"><div class="docente-avatar" aria-hidden="true">' +
            escape(_iniciales(perfil['nombre'])) + '</div><div><p>DOCENTE · MI PERFIL</p><h1>' +
            escape(perfil['nombre']) + '</h1><span>' + escape(perfil['usuario']) +
            '</span></div><aside><strong>' + str(len(perfil['proximas'])) +
            '</strong><span>próximas clases</span></aside></section>')
        st.html('<div class="docente-resumen"><span><strong>' + str(perfil['total_activas']) +
            '</strong> materias activas</span><span><strong>' + str(len(perfil['materias'])-perfil['total_activas']) +
            '</strong> archivadas</span><span><strong>' + str(perfil['confirmadas']) + '</strong> clases confirmadas</span></div>')
        agenda, materias = st.columns([1.2, 1], gap='large')
        with agenda, st.container(border=True):
            st.subheader('Agenda de clases')
            st.caption('Horarios creados · hora de Colombia. Programar una clase no registra asistencia.')
            hoy = hora_actual_colombia().date()
            if not isinstance(st.session_state.get('docente_mes'), date):
                st.session_state['docente_mes'] = hoy.replace(day=1)
            mes = st.session_state['docente_mes']
            with st.container(horizontal=True, vertical_alignment='center'):
                st.button('Mes anterior', key='docente_mes_anterior', icon=':material/chevron_left:',
                    type='tertiary', on_click=cambiar_mes_docente, args=(-1,), disabled=mes == date.min)
                st.html(f'<p class="perfil-mes-titulo">{MESES[mes.month-1].capitalize()} {mes.year}</p>')
                st.button('Mes siguiente', key='docente_mes_siguiente', icon=':material/chevron_right:',
                    type='tertiary', on_click=cambiar_mes_docente, args=(1,), disabled=mes.year == 9999 and mes.month == 12)
            st.html(html_calendario_docente(mes, perfil['dias'], hoy))
            fechas = [d for d in sorted(perfil['dias']) if (d.year, d.month) == (mes.year, mes.month)]
            if fechas:
                if st.session_state.get('docente_dia') not in fechas:
                    st.session_state.pop('docente_dia', None)
                dia = st.selectbox('Clases del día', fechas, key='docente_dia', format_func=lambda d: d.strftime('%d/%m/%Y'))
                _lista_clases(perfil['dias'][dia])
            else:
                st.info('No hay clases creadas en este mes.')
        with materias:
            st.subheader('Todas mis materias')
            st.caption('Tu catálogo académico; administra matrículas y asistencia desde el portal.')
            if not perfil['materias']:
                st.info('Aún no tienes materias.')
            for m in perfil['materias']:
                with st.container(border=True):
                    st.markdown('**' + escape(m['nombre']).replace('*', '\\*') + '**')
                    st.caption(f"{m['codigo']} · {m['seccion']} · {'Activa' if m['activa'] else 'Archivada'}")
                    st.write(f"{m['estudiantes']} estudiantes · {len(m['clases'])} clases creadas")
            st.subheader('Próximas sesiones')
            _lista_clases(perfil['proximas'][:10])
            if len(perfil['proximas']) > 10:
                st.caption('Se muestran las próximas diez; consulta el calendario para las demás.')


def pantalla_configuracion_docente():
    if not sesion_activa('profesor'):
        raise PermissionError('La configuración requiere una sesión docente.')
    encabezado_panel('profesor', autenticado=True)
    st.button('Volver a mi portal', key='config_docente_volver', type='tertiary',
        on_click=seleccionar_portal, args=('profesor',))
    introduccion('Cuenta docente · Configuración', 'Preferencias y gestión de cuenta',
        'Administra el archivo de tus materias y de tu cuenta con conservación del historial.')
    from src.componentes.gestion_cuenta import gestion_cuenta
    gestion_cuenta()
