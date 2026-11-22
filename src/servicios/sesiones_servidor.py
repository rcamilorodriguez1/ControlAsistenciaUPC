"""Registro unico compartido por todos los roles; tokens opacos, revocables y sin registros sensibles."""
from hashlib import sha256
import secrets
import oracledb
from src.base_datos.configuracion import obtener_conexion
from src.base_datos.consultas import cargar_sql


class SesionInvalida(PermissionError):
    pass


MENSAJES = {
    20200: 'La sesión no es válida. Inicia sesión nuevamente.',
    20201: 'Tu sesión fue reemplazada por un acceso desde otra pestaña, navegador o dispositivo.',
    20202: 'Esta sesión ya fue cerrada. Inicia sesión nuevamente.',
    20203: 'La sesión caducó. Inicia sesión nuevamente.',
    20204: 'Tu cuenta no está activa. Contacta con Gestión académica.',
    20205: 'Inicia sesión nuevamente para validar tu acceso en el servidor.',
    20206: 'La autorización excepcional ya no está vigente. Contacta con Gestión académica.',
}


def _parametros(rol, actor_id, token):
    if rol not in ('profesor','estudiante','administrador') or type(actor_id) is not int or actor_id<1:
        raise SesionInvalida(MENSAJES[20200])
    if not isinstance(token,str) or not 16<=len(token)<=128:
        raise SesionInvalida(MENSAJES[20200])
    return [rol.upper(), actor_id, sha256(token.encode('utf-8')).hexdigest()]


def _llamar(conn, nombre, parametros, *, esquema=''):
    try:
        with conn.cursor() as cur:
            cur.callproc(esquema+'pkg_sesiones.'+nombre, parametros)
    except oracledb.Error as exc:
        codigo=getattr(exc.args[0],'code',None)
        if codigo in MENSAJES: raise SesionInvalida(MENSAJES[codigo]) from None
        raise


def _operar(nombre, parametros):
    # Conexion directa: no invocar bd.ejecutar_con_reintentos ni recursar al contexto de sesion.
    with obtener_conexion() as conn:
        try:
            _llamar(conn,nombre,parametros)
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def abrir(rol, actor_id, hash_credencial=None, *, prueba_identidad=None):
    from src.servicios.autenticacion import exigir_acceso_disponible
    exigir_acceso_disponible()
    token=secrets.token_urlsafe(32)
    with obtener_conexion() as conn:
        try:
            _llamar(conn,'abrir',_parametros(rol,actor_id,token))
            if rol=='estudiante':
                from src.servicios.verificacion_identidad import confirmar_en_conexion
                confirmar_en_conexion(conn,actor_id,prueba_identidad)
            if rol=='profesor' and hash_credencial is not None:
                # El password pudo cambiar entre su verificacion y la apertura de sesion.
                # Se comprueba con SESION bloqueada antes de CUENTA, igual que la recuperacion.
                with conn.cursor() as cur:
                    cur.execute(cargar_sql('servicios/sesiones_servidor/abrir_01'),i=actor_id)
                    fila=cur.fetchone()
                    if fila is None or not secrets.compare_digest(str(fila[0]),str(hash_credencial)):
                        raise SesionInvalida('La contraseña cambió. Inicia sesión con la contraseña actual.')
            conn.commit()
        except Exception:
            conn.rollback()
            if rol=='estudiante':
                from src.servicios.verificacion_identidad import registrar_fallo_biometrico
                metodo=getattr(prueba_identidad,'metodo','BIOMETRIA')
                registrar_fallo_biometrico('PRUEBA_RECHAZADA',metodo=metodo,estudiante_id=actor_id)
            raise
    return token


def validar(rol, actor_id, token, *, renovar=False):
    _operar('validar',[*_parametros(rol,actor_id,token),int(renovar)])


def validar_en_conexion(conn, rol, actor_id, token, *, esquema=''):
    """Bloquea la sesion durante la operacion protegida, tambien en la conexion limitada del admin."""
    _llamar(conn,'validar',[*_parametros(rol,actor_id,token),0],esquema=esquema)


def cerrar(rol, actor_id, token):
    _operar('cerrar',_parametros(rol,actor_id,token))
