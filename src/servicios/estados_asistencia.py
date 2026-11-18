"""La ausencia es un resultado; sin muestra y fallo no son decisiones académicas."""

PRESENTE = 'PRESENTE'
AUSENTE = 'AUSENTE'
SIN_MUESTRA = 'SIN_MUESTRA'
ANALISIS_FALLIDO = 'ANALISIS_FALLIDO'
ETIQUETAS = {PRESENTE: 'Presente', AUSENTE: 'Ausente', SIN_MUESTRA: 'Sin muestra',
             ANALISIS_FALLIDO: 'Análisis fallido'}


def estado_deteccion(registro):
    valor = registro.get('presente')
    estado = registro.get('estado_deteccion')
    if estado is None and type(valor) is bool:
        estado = PRESENTE if valor else AUSENTE
    if estado in (PRESENTE, AUSENTE):
        if type(valor) is not bool or valor != (estado == PRESENTE):
            raise ValueError('La detección y su estado no coinciden.')
    elif estado in (SIN_MUESTRA, ANALISIS_FALLIDO):
        if valor is not None:
            raise ValueError('Una detección desconocida no puede equivaler a presencia o ausencia.')
    else:
        raise ValueError('El resultado de detección es inválido.')
    return estado
