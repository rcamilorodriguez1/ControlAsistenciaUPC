"""Métricas del perfil: una decisión confirmada por clase, sin inferir ausencias."""
from collections import defaultdict
from src.base_datos.perfil_estudiante import consultar_datos
from src.utilidades.fecha_hora import convertir_a_hora_colombia
from src.utilidades.sesiones import obtener_actor
from src.servicios.sesiones_servidor import SesionInvalida

# Referencias visuales editables; no son reglas de aprobación de asignaturas.
UMBRAL_EXCELENTE = 90
UMBRAL_ACEPTABLE = 80


def estado_porcentaje(porcentaje):
    if porcentaje is None:
        return {'clave': 'sin-registros', 'etiqueta': 'Sin registros'}
    if porcentaje >= UMBRAL_EXCELENTE:
        return {'clave': 'excelente', 'etiqueta': 'Excelente'}
    if porcentaje >= UMBRAL_ACEPTABLE:
        return {'clave': 'aceptable', 'etiqueta': 'Aceptable'}
    return {'clave': 'riesgo', 'etiqueta': 'En riesgo'}


def _resumen(presentes, ausentes):
    total = presentes + ausentes
    porcentaje = presentes / total * 100 if total else None
    return {'asistidas': presentes, 'ausencias': ausentes, 'total': total,
            'porcentaje': porcentaje, 'estado': estado_porcentaje(porcentaje)}


def construir_perfil(filas):
    if not filas:
        raise SesionInvalida('La cuenta del estudiante ya no está disponible.')
    estudiante_id = int(filas[0]['estudiante_id'])
    materias = {}
    registros = {}
    for fila in filas:
        if int(fila['estudiante_id']) != estudiante_id:
            raise PermissionError('Los datos no corresponden a un único estudiante.')
        materia_id = fila.get('materia_id')
        if materia_id is None:
            continue
        materia_id = int(materia_id)
        if materia_id not in materias:
            materias[materia_id] = {
                'materia_id': materia_id, 'nombre': fila['nombre_materia'],
                'codigo': fila['codigo_materia'], 'seccion': fila.get('seccion') or 'Sin grupo',
                'matriculada': fila['matriculada'] == 1, 'registros': [],
            }
        clase_id = fila.get('clase_id')
        if clase_id is None:
            continue
        if fila.get('presente') not in (0, 1) or fila.get('presente') is None:
            raise ValueError('La decisión de una clase confirmada es inválida.')
        clave = (materia_id, int(clase_id))
        fecha = convertir_a_hora_colombia(fila['fecha_clase'])
        registro = {'materia_id': materia_id, 'clase_id': int(clase_id),
                    'materia': materias[materia_id]['nombre'], 'fecha': fecha,
                    'presente': fila['presente'] == 1, 'corregido': fila.get('corregido_manual') == 1}
        if clave in registros and registros[clave] != registro:
            raise ValueError('Existen decisiones incompatibles para una misma clase.')
        registros[clave] = registro
    dias = defaultdict(list)
    for registro in sorted(registros.values(), key=lambda r: (r['fecha'], r['clase_id'])):
        materias[registro['materia_id']]['registros'].append(registro)
        dias[registro['fecha'].date()].append(registro)
    for materia in materias.values():
        asistidas = sum(r['presente'] for r in materia['registros'])
        materia.update(_resumen(asistidas, len(materia['registros']) - asistidas))
    presentes = sum(r['presente'] for r in registros.values())
    return {
        'estudiante_id': estudiante_id, 'nombre': filas[0]['nombre_estudiante'],
        'tipo_documento': filas[0].get('tipo_documento'),
        'documento_final': filas[0].get('documento_final'),
        'estado_verificacion': filas[0].get('estado_verificacion','PENDIENTE'),
        'total_materias': sum(m['matriculada'] for m in materias.values()),
        'materias': sorted(materias.values(), key=lambda m: (not m['matriculada'], m['nombre'].casefold())),
        'dias': dict(dias), **_resumen(presentes, len(registros) - presentes),
    }


def cargar_perfil_estudiante():
    actor = obtener_actor(renovar=True)
    if actor is None or actor[0] != 'estudiante':
        raise PermissionError('Inicia sesión como estudiante para consultar tu perfil.')
    filas = consultar_datos(actor[1])
    perfil = construir_perfil(filas)
    if perfil['estudiante_id'] != actor[1]:
        raise PermissionError('El perfil no pertenece a la sesión actual.')
    return perfil


def estado_dia(registros):
    if not registros:
        return 'sin-registros'
    presentes = sum(r['presente'] for r in registros)
    return 'presente' if presentes == len(registros) else 'ausente' if presentes == 0 else 'mixto'
