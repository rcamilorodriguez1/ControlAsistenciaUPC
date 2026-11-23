"""Escrituras autorizadas en PL/SQL, sin reintentos de COMMIT incierto."""
import oracledb
from src.base_datos import bd


def ejecutar(nombre, parametros, *, salida=False):
    if nombre not in {'crear_materia','matricular','retirar','archivar_materia','retirar_biometria','archivar_estudiante','archivar_profesor','actualizar_documento'}:
        raise ValueError('Operación no permitida.')
    def op(conn):
        try:
            with conn.cursor() as cur:
                args = list(parametros)
                if salida:
                    valor = cur.var(oracledb.NUMBER)
                    args.append(valor)
                cur.callproc('pkg_gestion.' + nombre, args)
                resultado = int(valor.getvalue()) if salida else 1
            conn.commit()
            return resultado
        except Exception:
            conn.rollback()
            raise
    try:
        return bd.ejecutar_con_reintentos(op, reintentos=1)
    except oracledb.Error as exc:
        codigo = getattr(exc.args[0], 'code', None)
        if codigo == 20085:
            raise PermissionError('La cuenta o el rol actual no permite esta operación.') from exc
        if codigo == 1 and nombre == 'actualizar_documento':
            raise ValueError('El documento ya está asociado a otra cuenta.') from exc
        if codigo in (1,20010,20088):
            raise ValueError('El código o la matrícula ya existe.') from exc
        if codigo in (20034,20035,20084,20086,20087,20303,20313):
            raise ValueError(str(exc.args[0]).splitlines()[0].split(': ',1)[-1]) from exc
        raise


def archivar_materia(materia_id, motivo): return ejecutar('archivar_materia',[materia_id,motivo])
def retirar_biometria(estudiante_id, motivo):
    resultado = ejecutar('retirar_biometria',[estudiante_id,motivo])
    from src.servicios.biometria_diferida import invalidar_modelo_facial
    invalidar_modelo_facial()
    return resultado
def archivar_estudiante(estudiante_id, motivo):
    resultado = ejecutar('archivar_estudiante',[estudiante_id,motivo])
    from src.servicios.biometria_diferida import invalidar_modelo_facial
    invalidar_modelo_facial()
    return resultado
def archivar_profesor(profesor_id, motivo): return ejecutar('archivar_profesor',[profesor_id,motivo])
