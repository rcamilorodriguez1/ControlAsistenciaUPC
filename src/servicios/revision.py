"""Valida la revision editable sin confiar en filas o identificadores del navegador."""

from src.servicios.estados_asistencia import estado_deteccion, SIN_MUESTRA, ANALISIS_FALLIDO

def preparar_revision(registros, revision=None):
    originales = {r['estudiante_id']: r for r in registros}
    if not originales or len(originales) != len(registros):
        raise ValueError('La propuesta tiene estudiantes duplicados o está vacía.')
    estados = {sid: estado_deteccion(r) for sid, r in originales.items()}
    if ANALISIS_FALLIDO in estados.values():
        raise ValueError('El análisis falló. No se puede confirmar esta propuesta; vuelve a analizar o usa otro método.')
    if revision is None:
        revision = [{'ID': r['estudiante_id'], 'Presente': r['presente'], 'Motivo': ''} for r in registros]
    vistos = set()
    resultado = []
    for fila in revision:
        sid = fila.get('ID')
        if isinstance(sid, bool) or sid not in originales or sid in vistos:
            raise ValueError('La revisión debe contener exactamente los estudiantes analizados.')
        vistos.add(sid)
        if 'Decisión' in fila:
            if fila['Decisión'] not in ('Presente', 'Ausente'):
                raise ValueError('Resuelve las decisiones pendientes antes de confirmar. Sin muestra no equivale a ausente.')
            presente = fila['Decisión'] == 'Presente'
        else:
            presente = fila.get('Presente')
        if type(presente) is not bool:
            raise ValueError('Selecciona presente o ausente para cada estudiante.')
        original = originales[sid]
        motivo = fila.get('Motivo', '')
        if not isinstance(motivo, str):
            raise ValueError('El motivo de corrección debe ser texto.')
        motivo = motivo.strip()
        cambiado = estados[sid] == SIN_MUESTRA or presente != original['presente']
        if cambiado and not (1 <= len(motivo) <= 500):
            raise ValueError('Explica cada cambio de asistencia con un motivo de 1 a 500 caracteres.')
        resultado.append({**original, 'presente_detectado': original['presente'],
                          'estado_deteccion': estados[sid], 'presente': presente,
                          'motivo_correccion': motivo if cambiado else None})
    if vistos != set(originales):
        raise ValueError('Faltan estudiantes en la revisión.')
    return sorted(resultado, key=lambda r: r['estudiante_id'])
