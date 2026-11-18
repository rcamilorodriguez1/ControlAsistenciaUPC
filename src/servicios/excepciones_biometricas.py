"""Gestión de excepciones únicamente mediante la conexión administrativa limitada."""
import oracledb

from src.base_datos import administracion as datos
from src.base_datos.bd import cifrar_contrasena, _filas_a_diccionarios
from src.servicios.validaciones import texto, codigo
from src.servicios.verificacion_identidad import huella_documento, CATEGORIAS


def _ejecutar(nombre, parametros, *, salida=False, identificador=False):
    def operacion(conn):
        with conn.cursor() as cur:
            argumentos = list(parametros)
            if identificador:
                valor = cur.var(oracledb.NUMBER)
                valor.setvalue(0, argumentos[0])
                argumentos[0] = valor
            if salida:
                with conn.cursor() as filas:
                    cur.callproc(datos.propietario() + '.pkg_excepciones.' + nombre, [*argumentos, filas])
                    return _filas_a_diccionarios(filas, filas.fetchall())
            cur.callproc(datos.propietario() + '.pkg_excepciones.' + nombre, argumentos)
            return int(valor.getvalue()) if identificador else None
    return datos._ejecutar(operacion, escritura=not salida)


def listar(busqueda=''):
    return _ejecutar('listar', [texto(busqueda, 'Búsqueda', 100, opcional=True)], salida=True)


def autorizar(estudiante_id, tipo, documento, contrasena, categoria, referencia, dias, *, version,
              documento_comprobado=False, nombre='', codigo_institucional=''):
    datos._actor()
    if not documento_comprobado:
        raise ValueError('Comprueba el documento oficial mediante el procedimiento institucional antes de autorizar.')
    if categoria not in CATEGORIAS or type(dias) is not int or not 1 <= dias <= 365:
        raise ValueError('Selecciona una categoría y una vigencia de 1 a 365 días.')
    if not isinstance(contrasena, str) or len(contrasena) < 12:
        raise ValueError('La contraseña alternativa debe tener al menos 12 caracteres.')
    if type(version) is not int or version < 0 or (estudiante_id is not None and (type(estudiante_id) is not int or estudiante_id < 1)):
        raise ValueError('Cuenta o versión no válida.')
    huella, final = huella_documento(tipo, documento)
    nombre = texto(nombre, 'Nombre', 200) if estudiante_id is None else None
    codigo_institucional = codigo(codigo_institucional, 'Código institucional') if estudiante_id is None else None
    return _ejecutar('autorizar', [estudiante_id, nombre, codigo_institucional, huella, tipo, final,
        cifrar_contrasena(contrasena), categoria, texto(referencia, 'Referencia del expediente', 100), dias, version], identificador=True)


def revocar(estudiante_id, motivo, *, version):
    if type(estudiante_id) is not int or estudiante_id < 1 or type(version) is not int or version < 0:
        raise ValueError('Cuenta o versión no válida.')
    return _ejecutar('revocar', [estudiante_id, version, texto(motivo, 'Motivo administrativo', 450)])
