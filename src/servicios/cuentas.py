import secrets
from src.configuracion import obtener_configuracion


def autorizar_alta_docente(codigo):
    esperado = obtener_configuracion('PROFESOR_CLAVE_ALTA')
    if not isinstance(esperado,str) or not esperado or not isinstance(codigo,str) or not secrets.compare_digest(codigo.encode('utf-8'),esperado.encode('utf-8')):
        raise ValueError('Se requiere el código privado de autorización docente del administrador.')
