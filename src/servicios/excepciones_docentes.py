"""Autorización docente mediante un paquete restringido y una sesión validada."""
import oracledb
from src.base_datos import administracion as datos
from src.base_datos.bd import cifrar_contrasena, _filas_a_diccionarios
from src.servicios.validaciones import texto
from src.servicios.verificacion_identidad import huella_documento, CATEGORIAS
from src.utilidades.sesiones import obtener_actor


def _actor():
    actor = obtener_actor(renovar=True)
    if actor is None or actor[0] != 'profesor':
        raise PermissionError('Se requiere una sesión docente vigente.')
    return actor


def _identificador(valor):
    if type(valor) is not int or valor < 1:
        raise ValueError('Cuenta o materia no válida.')
    return valor


def _ejecutar(nombre, parametros, *, lectura=False):
    actor = _actor()
    pool = datos.obtener_pool_admin()
    conn = pool.acquire()
    devolver = True
    try:
        from src.servicios.sesiones_servidor import validar_en_conexion
        validar_en_conexion(conn, *actor, esquema=datos.propietario()+'.')
        with conn.cursor() as cur:
            cur.callproc(datos.propietario()+'.pkg_auditoria.limpiar_contexto')
            cur.callproc(datos.propietario()+'.pkg_auditoria.establecer_contexto', ['PROFESOR', actor[1], None])
            if lectura:
                with conn.cursor() as filas:
                    cur.callproc(datos.propietario()+'.pkg_excepciones_docentes.'+nombre, [*parametros, filas])
                    return _filas_a_diccionarios(filas, filas.fetchall())
            cur.callproc(datos.propietario()+'.pkg_excepciones_docentes.'+nombre, parametros)
        conn.commit()
    except oracledb.Error as exc:
        codigo = getattr(exc.args[0], 'code', None)
        if codigo == 20311:
            raise PermissionError('La materia o la autorización no te pertenece, o la matrícula ya no está vigente.') from exc
        if codigo == 1:
            raise ValueError('El documento ya está asociado a otra cuenta.') from exc
        if codigo in (20301, 20302, 20303):
            raise ValueError(str(exc.args[0]).splitlines()[0].split(': ', 1)[-1]) from exc
        raise
    finally:
        try:
            conn.rollback()
            with conn.cursor() as cur:
                cur.callproc(datos.propietario()+'.pkg_auditoria.limpiar_contexto')
        except Exception:
            devolver = False
            pool.drop(conn)
        if devolver:
            pool.release(conn)


def listar(materia_id):
    return _ejecutar('listar', [_identificador(materia_id)], lectura=True)


def autorizar(materia_id, estudiante_id, tipo, documento, contrasena, categoria, referencia, dias,
              *, version, documento_comprobado=False):
    _actor()
    _identificador(materia_id)
    _identificador(estudiante_id)
    if not documento_comprobado:
        raise ValueError('Comprueba el documento del estudiante antes de autorizar.')
    if categoria not in CATEGORIAS or type(dias) is not int or not 1 <= dias <= 365:
        raise ValueError('Selecciona una categoría y una vigencia de 1 a 365 días.')
    if type(version) is not int or version < 0:
        raise ValueError('Versión no válida. Actualiza la consulta.')
    if not isinstance(contrasena, str) or len(contrasena) < 12:
        raise ValueError('La contraseña alternativa debe tener al menos 12 caracteres.')
    huella, final = huella_documento(tipo, documento)
    return _ejecutar('autorizar', [materia_id, estudiante_id, huella, tipo, final,
        cifrar_contrasena(contrasena), categoria, texto(referencia, 'Referencia de autorización', 100), dias, version])


def revocar(materia_id, estudiante_id, motivo, *, version):
    if type(version) is not int or version < 0:
        raise ValueError('Versión no válida. Actualiza la consulta.')
    return _ejecutar('revocar', [_identificador(materia_id), _identificador(estudiante_id), version,
        texto(motivo, 'Motivo', 450)])
