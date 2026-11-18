"""Identificación abierta: umbral absoluto y margen frente a otra identidad."""

from dataclasses import dataclass
import math

import numpy as np

from src.configuracion import obtener_configuracion
from src.utilidades.biometria import validar_vector_facial, normalizar_vector_voz


@dataclass(frozen=True)
class Coincidencia:
    identidad: object | None
    valor: float | None
    margen: float | None
    motivo: str


def parametros(modalidad, umbral=None, margen=None):
    prefijo = 'FACIAL' if modalidad == 'facial' else 'VOZ'
    defecto = 0.55 if modalidad == 'facial' else 0.65
    umbral = float(obtener_configuracion(f'{prefijo}_UMBRAL', defecto) if umbral is None else umbral)
    margen = float(obtener_configuracion(f'{prefijo}_MARGEN', 0.05) if margen is None else margen)
    limite = 2 if modalidad == 'facial' else 1
    if not math.isfinite(umbral) or not 0 < umbral <= limite or not math.isfinite(margen) or not 0 < margen <= limite:
        raise ValueError('Umbral y margen de reconocimiento inválidos.')
    return umbral, margen


class ClasificadorReferencias:
    def __init__(self, referencias, modalidad='facial'):
        if modalidad not in ('facial', 'voz'):
            raise ValueError('Modalidad inválida.')
        self.modalidad = modalidad
        validar = validar_vector_facial if modalidad == 'facial' else normalizar_vector_voz
        self.referencias = {sid: validar(vector).copy() for sid, vector in referencias.items()}
        for vector in self.referencias.values():
            vector.flags.writeable = False

    def identificar(self, vector, *, permitidos=None, umbral=None, margen=None):
        umbral, margen_minimo = parametros(self.modalidad, umbral, margen)
        consulta = (validar_vector_facial if self.modalidad == 'facial' else normalizar_vector_voz)(vector)
        if not self.referencias:
            return Coincidencia(None, None, None, 'SIN_REFERENCIAS')
        valores = [(sid, float(np.linalg.norm(ref - consulta)) if self.modalidad == 'facial'
                    else float(np.clip(np.dot(ref, consulta), -1, 1))) for sid, ref in self.referencias.items()]
        valores.sort(key=lambda r: r[1], reverse=self.modalidad == 'voz')
        sid, valor = valores[0]
        separacion = None if len(valores) == 1 else abs(valor - valores[1][1])
        pasa = valor <= umbral if self.modalidad == 'facial' else valor >= umbral
        if not pasa:
            return Coincidencia(None, valor, separacion, 'DESCONOCIDO')
        if separacion is not None and separacion < margen_minimo:
            return Coincidencia(None, valor, separacion, 'AMBIGUO')
        # Un perfil conocido ajeno a la materia nunca se reasigna al más parecido de su matrícula.
        if permitidos is not None and sid not in permitidos:
            return Coincidencia(None, valor, separacion, 'FUERA_DE_MATRICULA')
        return Coincidencia(sid, valor, separacion, 'COINCIDENCIA')
