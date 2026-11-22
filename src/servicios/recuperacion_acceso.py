"""Recuperacion docente con autorizacion privada, limites persistentes y revocacion atomica."""
from hashlib import sha256
import secrets
import oracledb

from src.base_datos import bd
from src.servicios.cuentas import autorizar_alta_docente
from src.servicios.validaciones import usuario as validar_usuario, clave as validar_clave
from src.base_datos.consultas import cargar_sql


def restablecer_profesor(usuario, autorizacion, nueva_clave, confirmacion):
    from src.servicios.autenticacion import exigir_acceso_disponible
    exigir_acceso_disponible()
    usuario = validar_usuario(usuario)
    validar_clave(nueva_clave)
    if nueva_clave != confirmacion:
        raise ValueError('La confirmación de contraseña no coincide.')
    try:
        autorizar_alta_docente(autorizacion)
        autorizado = True
    except ValueError:
        autorizado = False
    llave = sha256(('recuperacion:profesor:'+usuario).encode()).hexdigest()

    def operacion(conn):
        with conn.cursor() as cur:
            cur.execute(cargar_sql('compartidas/limpiar_limites_expirados'))
            try: cur.execute(cargar_sql('compartidas/crear_limite'),c=llave)
            except oracledb.IntegrityError as exc:
                if exc.args[0].code != 1: raise
            cur.execute(cargar_sql('compartidas/consultar_limites'),c=llave)
            intentos,bloqueado,expirada = cur.fetchone()
            if bloqueado:
                conn.commit();return False
            if expirada: intentos=0
            cur.execute(cargar_sql('servicios/recuperacion_acceso/operacion_03'),u=usuario)
            fila=cur.fetchone()
            correcto=autorizado and fila is not None
            if correcto:
                profesor_id=int(fila[0])
                cur.execute(cargar_sql('servicios/recuperacion_acceso/operacion_05'))
                # Crear una fila revocada si aun no existia permite respetar el orden de bloqueo
                # SESION -> CUENTA incluso frente al primer login concurrente de esa persona.
                try:
                    cur.execute(cargar_sql('servicios/recuperacion_acceso/operacion_09'),
                        i=profesor_id,h=sha256(secrets.token_bytes(32)).hexdigest())
                except oracledb.IntegrityError as exc:
                    if exc.args[0].code != 1:raise
                cur.execute(cargar_sql('servicios/recuperacion_acceso/operacion_06'),i=profesor_id)
                cur.fetchone()
                cur.execute(cargar_sql('servicios/recuperacion_acceso/operacion_07'),i=profesor_id)
                perfil=cur.fetchone()
                correcto=perfil is not None and perfil[0].strip().lower()==usuario and perfil[1]==1
                if not correcto:cur.execute(cargar_sql('servicios/recuperacion_acceso/operacion_10'))
                else:
                    cur.execute(cargar_sql('servicios/recuperacion_acceso/operacion_11'),h=bd.cifrar_contrasena(nueva_clave),i=profesor_id)
                    cur.execute(cargar_sql('servicios/recuperacion_acceso/operacion_12'),i=profesor_id)
                    cur.execute(cargar_sql('compartidas/limpiar_limite'),c=sha256(usuario.encode()).hexdigest())
                    cur.execute(cargar_sql('compartidas/limpiar_limite'),c=llave)
                    cur.execute(cargar_sql('servicios/recuperacion_acceso/operacion_15'),i=profesor_id)
            if not correcto:
                cur.execute(cargar_sql('compartidas/registrar_fallo_acceso'),
                    n=intentos+1,exp=expirada,c=llave)
        conn.commit()
        return bool(correcto)
    return bd.ejecutar_con_reintentos(operacion,reintentos=1)
