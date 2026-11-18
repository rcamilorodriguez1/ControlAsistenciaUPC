"""Sustituto de Oracle para pruebas de interfaz; la aplicacion no importa este modulo."""
import secrets
from unittest.mock import patch


def simular_sesiones(caso):
    p=patch('src.pantallas.pantalla_estudiante.acreditar_biometria',side_effect=lambda p:p)
    p.start();caso.addCleanup(p.stop)
    p=patch('src.pantallas.pantalla_estudiante.registrar_fallo_biometrico')
    p.start();caso.addCleanup(p.stop)
    for nombre,kw in [('abrir',{'side_effect':lambda *a,**kw:secrets.token_urlsafe(32)}),
                       ('validar',{'return_value':None}),('cerrar',{'return_value':None})]:
        p=patch('src.servicios.sesiones_servidor.'+nombre,**kw)
        p.start();caso.addCleanup(p.stop)
