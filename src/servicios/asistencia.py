"""Confirmación de la propuesta vigente, con revalidación en Oracle."""

from src.base_datos.bd import crear_asistencia
from src.utilidades.sesiones import obtener_resultado, invalidar_resultado, reiniciar_toma
from src.servicios.revision import preparar_revision


def confirmar_resultado(resultado_id, estado=None, *, revision=None):
    resultado = obtener_resultado(resultado_id, estado)
    if resultado is None:
        raise PermissionError("Esta propuesta ya no pertenece a la sesión y materia actuales.")
    if resultado['contexto'].get('clase_id') is None:
        raise ValueError('Selecciona una clase y ejecuta nuevamente el análisis.')
    registros = preparar_revision(resultado['registros'], revision)
    # Consumir antes de escribir: una segunda pulsación no reutiliza la propuesta.
    invalidar_resultado(estado)
    cantidad = crear_asistencia(registros, profesor_id=resultado["contexto"]["profesor_id"],
                                clase_id=resultado['contexto']['clase_id'],
                                clave_confirmacion=resultado_id, origen=resultado['origen'])
    reiniciar_toma(estado)
    return cantidad
