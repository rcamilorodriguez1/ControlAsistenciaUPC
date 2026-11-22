import base64
from functools import lru_cache
from html import escape
import streamlit as st
from src.interfaz.diseno_base import RAIZ
from src.interfaz.navegacion import abrir_perfil, abrir_configuracion_docente
from src.utilidades.sesiones import salir_al_portal, seleccionar_portal, ir_al_inicio, obtener_actor


@lru_cache(maxsize=1)
def _imagen_logo():
    logo = (RAIZ / 'static' / 'img' / 'upc' / 'logo-horizontal-manual.jpg').read_bytes()
    imagen = 'data:image/jpeg;base64,' + base64.b64encode(logo).decode('ascii')
    return imagen


@lru_cache(maxsize=1)
def _foco_cuenta():
    scripts = ('cuenta.js', 'diseno.js')
    return '<script>' + '\n'.join((RAIZ / 'static/js' / nombre).read_text(encoding='utf-8') for nombre in scripts) + '</script>'


def _marca():
    with st.container(key='marca_institucional',width='content',horizontal=True,wrap=False,vertical_alignment='center',gap=None):
        with st.container(key='logo_inicio',width='content'):
            etiqueta = f'![Ir al inicio]({_imagen_logo()})'
            if '_pagina_inicio' in st.session_state:
                st.page_link(st.session_state['_pagina_inicio'],label=etiqueta,icon='',help='Ir al inicio')
            else:
                # Vistas sinteticas aisladas, sin router ni acceso a Oracle.
                st.button(etiqueta,key='logo_inicio_vista',on_click=ir_al_inicio,type='tertiary')
        st.html('<div class="upc-platform-name"><div class="upc-brand-title">UPC <span aria-hidden="true">|</span> Aula</div>'
            '<div class="upc-brand-subtitle">Universidad Popular del Cesar</div></div>' + _foco_cuenta(),
            width='content', unsafe_allow_javascript=True)


def ir_a_inicio():
    ir_al_inicio()


@lru_cache(maxsize=2)
def icono_portal(rol):
    if rol not in ('estudiante', 'profesor'): raise ValueError('Portal inválido.')
    svg = (RAIZ / 'static' / 'img' / f'icono-{rol}.svg').read_bytes()
    return '<img alt="" src="data:image/svg+xml;base64,' + base64.b64encode(svg).decode('ascii') + '">'


def encabezado_inicio():
    _encabezado(es_inicio=True)


def _encabezado(*, es_inicio=False):
    with st.container(key='barra_panel', horizontal=True, horizontal_alignment='distribute',
                      vertical_alignment='center', gap='small'):
        _marca()
        _acciones_cuenta(es_inicio=es_inicio)


def _acciones_cuenta(*, es_inicio=False):
    with st.container(key='acciones_cabecera', width='content', horizontal=True, wrap=False,
                      horizontal_alignment='right', vertical_alignment='center', gap='small'):
        if es_inicio:
            st.button('Gestión académica', type='tertiary', width='content',
                icon=':material/school:', key='acceso_gestion_academica',
                on_click=seleccionar_portal, args=('administrador',), help='Acceso administrativo: cuentas, materias y auditoría.')
        else:
            with st.container(key='navegacion_inicio', width='content'):
                if '_pagina_inicio' in st.session_state:
                    st.page_link(st.session_state['_pagina_inicio'], label='Inicio', icon=':material/home:')
                else:
                    st.button('Inicio', key='inicio_panel', on_click=ir_al_inicio, type='tertiary', icon=':material/home:')
        actor = obtener_actor()
        if actor:
            nombres = {'profesor': 'Docente', 'estudiante': 'Estudiante', 'administrador': 'Administrativo'}
            with st.popover(nombres[actor[0]], icon=':material/account_circle:', type='tertiary', key='menu_cuenta'):
                with st.container(key='opciones_cuenta', gap=None):
                    st.button('Mi perfil', icon=':material/person:', type='tertiary',
                              disabled=actor[0] not in ('estudiante', 'profesor'), key='mi_perfil_cuenta',
                              help='Ver mi actividad académica',
                              width='stretch', on_click=abrir_perfil)
                    st.button('Configuración', icon=':material/settings:', type='tertiary',
                              disabled=actor[0] != 'profesor', key='configuracion_cuenta',
                              help='Administrar cuenta y materias' if actor[0] == 'profesor' else 'Próximamente',
                              width='stretch', on_click=abrir_configuracion_docente)
                    with st.container(key='cierre_cuenta', gap=None):
                        st.divider()
                        st.button('Cerrar sesión', icon=':material/logout:', type='tertiary',
                                  key='loginbackbtn', width='stretch',
                                  on_click=salir_al_portal, args=(st.session_state.get('tipo_sesion'),))


def encabezado_panel(rol=None, *, autenticado=False):
    _encabezado()


def introduccion(etiqueta, titulo, descripcion):
    st.html('<div class="upc-page-intro"><div class="upc-eyebrow">' + escape(etiqueta) + '</div><h1>' +
            escape(titulo) + '</h1><p>' + escape(descripcion) + '</p></div>')
