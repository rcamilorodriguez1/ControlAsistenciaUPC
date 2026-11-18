"""Datos académicos sintéticos del perfil; nunca se importan desde la aplicación."""


def filas_perfil(estudiante_id=990007):
    comunes = {'estudiante_id': estudiante_id, 'nombre_estudiante': 'Estudiante de prueba',
               'codigo_institucional': 'PRUEBA-2026', 'corregido_manual': 0}
    filas = []
    for materia_id, nombre, total, presentes, matriculada in (
        (10, 'Bases de Datos', 10, 8, 1),
        (20, 'Ingeniería de Software', 10, 9, 1),
        (30, 'Cálculo diferencial', 4, 2, 1),
        (40, 'Lectura académica', 0, 0, 1),
        (99, 'Historia de la tecnología', 2, 2, 0),
    ):
        base = {**comunes, 'materia_id': materia_id, 'nombre_materia': nombre,
                'codigo_materia': f'PRUEBA-{materia_id}', 'seccion': 'Grupo 01', 'matriculada': matriculada}
        if not total:
            filas.append({**base, 'clase_id': None, 'presente': None, 'fecha_clase': None})
        for i in range(total):
            dia = i + 1 if materia_id != 30 else (3, 5, 7, 9)[i]
            mes = 10 if materia_id == 99 else 11
            hora = 8 if materia_id == 10 else 10 if materia_id == 20 else 14
            filas.append({**base, 'clase_id': materia_id * 100 + i,
                          'presente': int(i < presentes),
                          'fecha_clase': f'2026-{mes:02}-{dia:02}T{hora:02}:00:00.000000-05:00'})
    return filas
