"""Contrato de los descriptores: dlib 128D sin reescalado; voz 256D con norma L2 unitaria."""

import numpy as np


class MuestraInvalida(ValueError):
    def __init__(self, mensaje, codigo='MUESTRA_INVALIDA'):
        super().__init__(mensaje)
        self.codigo = codigo


def _vector(valores, dimensiones, etiqueta):
    try:
        vector = np.asarray(valores)
        if vector.shape != (dimensiones,) or vector.dtype.kind not in 'fiu':
            raise ValueError
        if any(isinstance(v, (bool, np.bool_)) for v in valores):
            raise ValueError
        vector = vector.astype(np.float64)
        with np.errstate(over='ignore', invalid='ignore'):
            norma = np.linalg.norm(vector)
        if not np.isfinite(vector).all() or not np.isfinite(norma) or norma <= 1e-12:
            raise ValueError
    except (ValueError, TypeError, OverflowError):
        raise MuestraInvalida(f'La muestra de {etiqueta} debe tener {dimensiones} valores numéricos finitos y no ser nula.',
                              'VECTOR_INVALIDO') from None
    return vector


def validar_vector_facial(valores):
    # Normalizar dlib alteraria las distancias del modelo y sus umbrales existentes.
    return _vector(valores, 128, 'rostro')


def normalizar_vector_voz(valores):
    vector = _vector(valores, 256, 'voz')
    return vector / np.linalg.norm(vector)
