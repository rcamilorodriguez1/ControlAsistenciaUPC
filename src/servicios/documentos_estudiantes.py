"""Documento estudiantil único; solo se conserva su HMAC y últimos caracteres."""
from src.base_datos import bd, gestion, administracion
from src.base_datos.consultas import cargar_sql
from src.servicios.verificacion_identidad import huella_documento
from src.utilidades.sesiones import obtener_actor


def etiqueta_documento(tipo=None, final=None):
    return f'{tipo} · ****{final}' if tipo and final else 'Documento pendiente'


def consultar_propio():
    actor = obtener_actor(renovar=True)
    if actor is None or actor[0] != 'estudiante':
        raise PermissionError('Inicia sesión como estudiante para consultar tu documento.')
    def operacion(conn):
        with conn.cursor() as cur:
            cur.execute(cargar_sql('base_datos/perfil_estudiante/documento_01'), i=actor[1])
            fila = cur.fetchone()
            if fila is None:
                raise PermissionError('La cuenta ya no está disponible.')
            return {'tipo':fila[0], 'final':fila[1], 'version':int(fila[2])}
    return bd.ejecutar_con_reintentos(operacion)


def guardar_propio(tipo, numero, *, version, comprobado=False):
    actor = obtener_actor(renovar=True)
    if actor is None or actor[0] != 'estudiante':
        raise PermissionError('Se requiere la sesión del estudiante.')
    return _guardar(actor[1], tipo, numero, version, comprobado, False)


def guardar_administrativo(estudiante_id, tipo, numero, *, version, comprobado=False):
    administracion._actor()
    return _guardar(estudiante_id, tipo, numero, version, comprobado, True)


def _guardar(estudiante_id, tipo, numero, version, comprobado, es_admin):
    if type(estudiante_id) is not int or estudiante_id < 1 or type(version) is not int or version < 0:
        raise ValueError('Cuenta o versión no válida.')
    if not comprobado:
        raise ValueError('Confirma la correspondencia del documento con la cuenta.')
    huella, final = huella_documento(tipo, numero)
    argumentos = [estudiante_id, huella, tipo, final, version]
    if es_admin:
        return administracion._escritura('actualizar_documento', argumentos)
    return gestion.ejecutar('actualizar_documento', argumentos)
