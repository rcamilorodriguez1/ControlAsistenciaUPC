"""Perfil académico privado: identidad, resumen, materias y calendario mensual."""
import calendar
from string import punctuation
from datetime import date
from html import escape

import streamlit as st

from src.componentes.encabezado import encabezado_panel
from src.servicios.perfil_estudiante import (
    cargar_perfil_estudiante, estado_dia, UMBRAL_EXCELENTE, UMBRAL_ACEPTABLE,
)
from src.servicios.sesiones_servidor import SesionInvalida
from src.utilidades.fecha_hora import hora_actual_colombia
from src.utilidades.sesiones import sesion_activa, seleccionar_portal

MESES = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
         'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')
DIAS = ('Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom')


def _e(valor):
    return escape(str(valor))


def _porcentaje(valor):
    return '—' if valor is None else f'{valor:.1f}'.replace('.', ',').removesuffix(',0')


def _iniciales(nombre):
    palabras = str(nombre).split()
    return ''.join(p[0] for p in (palabras[:1] + palabras[-1:] if len(palabras) > 1 else palabras)).upper()


def _identidad(perfil):
    porcentaje = perfil['porcentaje']
    valor = 0 if porcentaje is None else min(100, max(0, porcentaje))
    estado = perfil['estado']
    codigo = f'Código institucional · {_e(perfil["codigo"])}' if perfil['codigo'] else 'Universidad Popular del Cesar'
    base = (f'{perfil["asistidas"]} de {perfil["total"]} clases con registro confirmado'
            if perfil['total'] else 'Aún no hay clases con registro confirmado')
    texto = _porcentaje(porcentaje)
    st.html(
        '<section class="perfil-portada" aria-label="Mi perfil académico">'
        '<div class="perfil-banner" aria-hidden="true"></div>'
        f'<div class="perfil-identidad"><div class="perfil-avatar" aria-hidden="true">{_e(_iniciales(perfil["nombre"]))}</div>'
        '<p class="perfil-rol">ESTUDIANTE · MI PERFIL</p>'
        f'<h1>{_e(perfil["nombre"])}</h1><p class="perfil-codigo">{codigo}</p></div>'
        '<aside class="perfil-asistencia"><h2>Asistencia general</h2>'
        f'<div class="perfil-circulo" role="img" aria-label="Asistencia acumulada: {texto}{" por ciento" if porcentaje is not None else "; sin registros"}" '
        f'style="--perfil-porcentaje:{valor:.4f}%"><div><strong>{texto}</strong>'
        f'<span>{"% acumulado" if porcentaje is not None else "sin registros"}</span></div></div>'
        f'<span class="perfil-estado perfil-estado--{estado["clave"]}">{_e(estado["etiqueta"])}</span>'
        f'<p class="perfil-base">{base}</p></aside></section>'
    )
    metricas = (
        ('Materias matriculadas', perfil['total_materias'], 'Inscripciones actuales'),
        ('Clases asistidas', perfil['asistidas'], 'Presencia confirmada'),
        ('Clases perdidas', perfil['ausencias'], 'Ausencia confirmada'),
        ('Clases con registro', perfil['total'], 'Todas tus materias'),
    )
    st.html('<section class="perfil-metricas" aria-label="Resumen global de asistencia">' + ''.join(
        f'<div><span>{titulo}</span><strong>{numero}</strong><small>{ayuda}</small></div>'
        for titulo, numero, ayuda in metricas) + '</section>')


def html_calendario(mes, dias, hoy=None):
    hoy = hoy or hora_actual_colombia().date()
    celdas = []
    for semana in calendar.Calendar(firstweekday=0).monthdayscalendar(mes.year, mes.month):
        fila = []
        for numero in semana:
            if not numero:
                fila.append('<td class="perfil-dia-fuera" aria-hidden="true"></td>')
                continue
            dia = date(mes.year, mes.month, numero)
            registros = dias.get(dia, [])
            estado = estado_dia(registros)
            presentes = sum(r['presente'] for r in registros)
            descripcion = (f'{presentes} asistencias y {len(registros)-presentes} ausencias'
                           if registros else 'Sin registros de asistencia')
            etiqueta = f'{numero} de {MESES[mes.month-1]} de {mes.year}: {descripcion}'
            actual = ' aria-current="date"' if dia == hoy else ''
            indicador = f'{presentes}/{len(registros)}' if registros else '—'
            fila.append(f'<td class="perfil-dia perfil-dia--{estado}" data-dia="{dia.isoformat()}" '
                        f'data-estado="{estado}" title="{_e(etiqueta)}" aria-label="{_e(etiqueta)}"{actual}>'
                        f'<span class="perfil-dia-numero">{numero}</span><span class="perfil-dia-cuenta">{indicador}</span></td>')
        celdas.append('<tr>' + ''.join(fila) + '</tr>')
    return (f'<table class="perfil-calendario" aria-label="Asistencia de {MESES[mes.month-1]} de {mes.year}">'
            '<thead><tr>' + ''.join(f'<th scope="col">{dia}</th>' for dia in DIAS) + '</tr></thead>'
            '<tbody>' + ''.join(celdas) + '</tbody></table>')


def cambiar_mes(delta):
    mes = st.session_state.get('perfil_mes', hora_actual_colombia().date().replace(day=1))
    indice = (mes.year - 1) * 12 + mes.month - 1 + delta
    if not 0 <= indice < 9999 * 12:
        return
    anio, numero = divmod(indice, 12)
    st.session_state['perfil_mes'] = date(anio + 1, numero + 1, 1)
    st.session_state.pop('perfil_dia', None)


def _registros_html(registros):
    return '<ul class="perfil-registros">' + ''.join(
        '<li><div><strong>' + _e(r['materia']) + '</strong><small>' +
        r['fecha'].strftime('%d/%m/%Y · %H:%M') + ' · Colombia' + '</small></div>' +
        f'<span class="perfil-registro-{"presente" if r["presente"] else "ausente"}">' +
        ('Asistió' if r['presente'] else 'No asistió') + '</span></li>'
        for r in registros) + '</ul>'


def _calendario(perfil):
    with st.container(key='perfil_calendario', border=True):
        st.subheader('Calendario de asistencia')
        hoy = hora_actual_colombia().date()
        if not isinstance(st.session_state.get('perfil_mes'), date):
            st.session_state['perfil_mes'] = hoy.replace(day=1)
        mes = st.session_state['perfil_mes'].replace(day=1)
        with st.container(key='perfil_calendario_controles', horizontal=True, wrap=False,
                          vertical_alignment='center', gap='small'):
            st.button('Mes anterior', icon=':material/chevron_left:', type='tertiary',
                      key='perfil_mes_anterior', on_click=cambiar_mes, args=(-1,),
                      disabled=mes.year == 1 and mes.month == 1)
            st.html(f'<p class="perfil-mes-titulo" aria-live="polite">{MESES[mes.month-1].capitalize()} {mes.year}</p>')
            st.button('Mes siguiente', icon=':material/chevron_right:', type='tertiary',
                      key='perfil_mes_siguiente', on_click=cambiar_mes, args=(1,),
                      disabled=mes.year == 9999 and mes.month == 12)
        st.html(html_calendario(mes, perfil['dias'], hoy))
        st.html('<div class="perfil-leyenda" aria-label="Estados del calendario">'
                '<span class="perfil-leyenda-presente">Asistió a todas</span>'
                '<span class="perfil-leyenda-ausente">No asistió</span>'
                '<span class="perfil-leyenda-mixto">Día mixto</span>'
                '<span class="perfil-leyenda-neutro">Sin registros</span></div>')
        fechas = sorted((d for d in perfil['dias'] if (d.year, d.month) == (mes.year, mes.month)), reverse=True)
        if fechas:
            if st.session_state.get('perfil_dia') not in fechas:
                st.session_state.pop('perfil_dia', None)
            dia = st.selectbox('Detalle del día', fechas, key='perfil_dia',
                               format_func=lambda d: f'{d.day} de {MESES[d.month-1]} · {len(perfil["dias"][d])} clases')
            st.html(_registros_html(perfil['dias'][dia]))
        else:
            st.caption('No hay asistencias registradas en este mes. Los días sin registro no se cuentan como ausencias.')


def _materias(perfil):
    with st.container(key='perfil_materias'):
        st.subheader('Mis materias')
        st.caption('Materias matriculadas y con historial. Despliega cada una para ver su asistencia.')
        if not perfil['total_materias']:
            st.info('Actualmente no tienes materias matriculadas.')
        if not perfil['materias']:
            return
        for materia in perfil['materias']:
            porcentaje = _porcentaje(materia['porcentaje'])
            texto = porcentaje + ' %' if materia['porcentaje'] is not None else 'Sin registros'
            nombre = materia['nombre'].translate(str.maketrans({c: chr(92) + c for c in punctuation}))
            estado = materia['estado']
            titulo = f'{nombre} · {texto} · {estado["etiqueta"]}'
            if materia['porcentaje'] is None:
                titulo = f'{nombre} · Sin registros'
            if not materia['matriculada']:
                titulo += ' · Histórica'
            with st.expander(titulo):
                st.caption(f'{materia["codigo"]} · {materia["seccion"]} · ' +
                           ('Matriculada' if materia['matriculada'] else 'Histórica · sin matrícula actual'))
                valor = materia['porcentaje'] or 0
                st.html(f'<div class="perfil-materia-estado"><strong>{texto}</strong>'
                        f'<span class="perfil-estado perfil-estado--{estado["clave"]}">{estado["etiqueta"]}</span></div>'
                        f'<div class="perfil-barra" role="img" aria-label="Asistencia: {texto}"><span style="width:{valor:.4f}%"></span></div>'
                        f'<p class="perfil-materia-cuentas">{materia["asistidas"]} asistidas · {materia["ausencias"]} ausencias · {materia["total"]} con registro</p>')
                if materia['registros']:
                    st.caption('Últimas clases registradas')
                    st.html(_registros_html(list(reversed(materia['registros'][-3:]))))
        st.caption(f'Referencia visual: excelente ≥ {UMBRAL_EXCELENTE} %, aceptable ≥ {UMBRAL_ACEPTABLE} % y en riesgo por debajo. '
                   'El acumulado incluye el historial de todas tus materias con registros confirmados.')


def pantalla_perfil_estudiante():
    if not sesion_activa('estudiante'):
        raise PermissionError('Este perfil requiere una sesión de estudiante.')
    encabezado_panel('estudiante', autenticado=True)
    st.button('Volver a mi portal', type='tertiary', icon=':material/arrow_back:',
              key='perfil_volver_portal', on_click=seleccionar_portal, args=('estudiante',))
    try:
        perfil = cargar_perfil_estudiante()
    except SesionInvalida:
        raise
    except PermissionError:
        st.error('No se pudo autorizar la consulta de tu perfil. Vuelve a tu portal e intenta nuevamente.')
        return
    with st.container(key='perfil_estudiante'):
        _identidad(perfil)
        from src.componentes.estado_verificacion import mostrar_estado_verificacion
        mostrar_estado_verificacion(perfil.get('estado_verificacion'))
        with st.container(key='perfil_detalle'):
            calendario, materias = st.columns([1.2, 1], gap='large')
            with calendario:
                _calendario(perfil)
            with materias:
                _materias(perfil)
