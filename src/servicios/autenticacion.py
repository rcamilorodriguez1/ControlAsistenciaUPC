"""Exclusividad de identidad en la sesión web identificada por el servidor."""
from streamlit.runtime.scriptrunner import get_script_run_ctx


class ConflictoSesion(PermissionError):
    """Un login no puede sustituir silenciosamente la identidad autenticada."""


def exigir_acceso_disponible():
    if get_script_run_ctx(suppress_warning=True) is None:
        return  # Las herramientas de consola no representan sesiones web.
    from src.utilidades.sesiones import obtener_actor
    if obtener_actor() is not None:
        raise ConflictoSesion('Cierra la sesión actual antes de autenticar otra cuenta.')
