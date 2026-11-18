from html import escape
import streamlit as st
from src.servicios.seguridad_claves import evaluar_clave


def mostrar_fortaleza(contrasena, *, usuario='', nombre=''):
    evaluacion = evaluar_clave(contrasena, usuario=usuario, nombre=nombre)
    nivel = evaluacion.puntuacion
    clase = f'clave-nivel-{nivel}' if nivel is not None else 'clave-sin-evaluar'
    if evaluacion.etiqueta == 'No válida': clase = 'clave-invalida'
    segmentos = ''.join('<span class="clave-segmento' + (' activo' if nivel is not None and i <= nivel else '') + '"></span>' for i in range(5))
    consejos = ''.join('<li>' + escape(c) + '</li>' for c in evaluacion.consejos)
    st.html('<div class="clave-fortaleza ' + clase + '" data-testid="clave-fortaleza" role="status" aria-live="polite">'
            '<div class="clave-medidor" aria-hidden="true">' + segmentos + '</div>'
            '<p class="clave-etiqueta">Fortaleza: ' + escape(evaluacion.etiqueta) + '</p>'
            + ('<ul class="clave-consejos">' + consejos + '</ul>' if consejos else '') + '</div>')


def mostrar_coincidencia(contrasena, confirmacion):
    if not confirmacion:
        clase, mensaje = 'clave-pendiente', 'Repite la misma contraseña para confirmarla.'
    elif contrasena == confirmacion:
        clase, mensaje = 'clave-coincide', 'Las contraseñas coinciden.'
    else:
        clase, mensaje = 'clave-no-coincide', 'Las contraseñas no coinciden.'
    st.html('<p class="clave-confirmacion ' + clase + '" data-testid="clave-confirmacion" role="status" aria-live="polite">' + mensaje + '</p>')
