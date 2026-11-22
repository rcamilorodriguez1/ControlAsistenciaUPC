"""Agenda del docente; un borrador es una clase programada, nunca asistencia."""
from collections import defaultdict
from src.base_datos.perfil_docente import consultar_datos
from src.servicios.sesiones_servidor import SesionInvalida
from src.utilidades.fecha_hora import convertir_a_hora_colombia, hora_actual_colombia
from src.utilidades.sesiones import obtener_actor


def construir_perfil(filas, ahora=None):
    if not filas:
        raise SesionInvalida('La cuenta del docente ya no está disponible.')
    ahora = ahora or hora_actual_colombia()
    profesor_id = int(filas[0]['profesor_id'])
    materias, clases = {}, {}
    for fila in filas:
        if int(fila['profesor_id']) != profesor_id:
            raise PermissionError('La agenda contiene datos de otro docente.')
        if fila.get('materia_id') is None:
            continue
        mid = int(fila['materia_id'])
        materias.setdefault(mid, dict(materia_id=mid, nombre=fila['nombre_materia'],
            codigo=fila['codigo_materia'], seccion=fila.get('seccion') or 'Sin grupo',
            activa=fila['materia_activa'] == 1, estudiantes=int(fila['total_estudiantes']), clases=[]))
        if fila.get('clase_id') is None:
            continue
        cid = int(fila['clase_id'])
        clase = dict(clase_id=cid, materia_id=mid, materia=materias[mid]['nombre'],
            fecha=convertir_a_hora_colombia(fila['fecha_clase']), estado=fila['estado'],
            activa=materias[mid]['activa'])
        if cid in clases and clases[cid] != clase:
            raise ValueError('Hay horarios incompatibles para una misma clase.')
        clases[cid] = clase
    dias = defaultdict(list)
    ordenadas = sorted(clases.values(), key=lambda c: (c['fecha'], c['clase_id']))
    for clase in ordenadas:
        materias[clase['materia_id']]['clases'].append(clase)
        dias[clase['fecha'].date()].append(clase)
    proximas = [c for c in ordenadas if c['activa'] and c['estado'] == 'BORRADOR' and c['fecha'] >= ahora]
    return dict(profesor_id=profesor_id, nombre=filas[0]['nombre_profesor'], usuario=filas[0]['usuario'],
        materias=list(materias.values()), dias=dict(dias), proximas=proximas,
        total_activas=sum(m['activa'] for m in materias.values()),
        confirmadas=sum(c['estado'] == 'CONFIRMADA' for c in ordenadas))


def cargar_perfil_docente():
    actor = obtener_actor(renovar=True)
    if actor is None or actor[0] != 'profesor':
        raise PermissionError('Inicia sesión como docente para consultar tu agenda.')
    perfil = construir_perfil(consultar_datos(actor[1]))
    if perfil['profesor_id'] != actor[1]:
        raise PermissionError('El perfil no pertenece a la sesión actual.')
    return perfil
