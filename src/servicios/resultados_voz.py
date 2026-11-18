from src.servicios.estados_asistencia import PRESENTE, AUSENTE, SIN_MUESTRA, ANALISIS_FALLIDO, ETIQUETAS


def construir_resultados_voz(estudiantes, materia_id, analisis, fecha):
    """Propuesta completa: resultados desconocidos permanecen sin decisión."""
    filas, registros = [], []
    for estudiante in estudiantes:
        sid = estudiante['estudiante_id']
        muestra = estudiante.get('embedding_voz')
        if analisis.estado == 'FALLIDO':
            estado, presente = ANALISIS_FALLIDO, None
        elif muestra is None or len(muestra) == 0:
            estado, presente = SIN_MUESTRA, None
        elif analisis.estado == 'SIN_MUESTRAS':
            # Un resultado incoherente tampoco se interpreta como ausencia.
            estado, presente = ANALISIS_FALLIDO, None
        else:
            presente = sid in analisis.puntajes
            estado = PRESENTE if presente else AUSENTE
        puntaje = analisis.puntajes.get(sid)
        filas.append({'Nombre': estudiante['nombre'], 'ID': sid, 'Estado': ETIQUETAS[estado],
                      'Puntaje': f'{puntaje:.2f}' if puntaje is not None else '-'})
        registros.append({'fecha_hora': fecha, 'materia_id': materia_id, 'estudiante_id': sid,
                          'presente': presente, 'estado_deteccion': estado})
    return filas, registros
