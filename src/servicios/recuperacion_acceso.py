"""Recuperacion docente con autorizacion privada, limites persistentes y revocacion atomica."""
from hashlib import sha256
import secrets
import oracledb

from src.base_datos import bd
from src.servicios.cuentas import autorizar_alta_docente
from src.servicios.validaciones import usuario as validar_usuario, clave as validar_clave


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
            cur.execute("DELETE FROM limites_acceso WHERE ventana_en<SYSTIMESTAMP-INTERVAL '1' DAY AND (bloqueado_hasta IS NULL OR bloqueado_hasta<SYSTIMESTAMP)")
            try: cur.execute('INSERT INTO limites_acceso(clave) VALUES(:c)',c=llave)
            except oracledb.IntegrityError as exc:
                if exc.args[0].code != 1: raise
            cur.execute("""SELECT intentos,CASE WHEN bloqueado_hasta>SYSTIMESTAMP THEN 1 ELSE 0 END,
                CASE WHEN ventana_en<SYSTIMESTAMP-INTERVAL '15' MINUTE THEN 1 ELSE 0 END
                FROM limites_acceso WHERE clave=:c FOR UPDATE""",c=llave)
            intentos,bloqueado,expirada = cur.fetchone()
            if bloqueado:
                conn.commit();return False
            if expirada: intentos=0
            cur.execute('SELECT profesor_id FROM profesores WHERE LOWER(TRIM(usuario))=:u AND activo=1',u=usuario)
            fila=cur.fetchone()
            correcto=autorizado and fila is not None
            if correcto:
                profesor_id=int(fila[0])
                cur.execute('SAVEPOINT recuperar_clave')
                # Crear una fila revocada si aun no existia permite respetar el orden de bloqueo
                # SESION -> CUENTA incluso frente al primer login concurrente de esa persona.
                try:
                    cur.execute("""INSERT INTO sesiones_usuario(rol,actor_id,token_hash,creada_en,actividad_en,expira_en,revocada_en)
                        VALUES('PROFESOR',:i,:h,SYSTIMESTAMP,SYSTIMESTAMP,SYSTIMESTAMP+INTERVAL '8' HOUR,SYSTIMESTAMP)""",
                        i=profesor_id,h=sha256(secrets.token_bytes(32)).hexdigest())
                except oracledb.IntegrityError as exc:
                    if exc.args[0].code != 1:raise
                cur.execute("SELECT actor_id FROM sesiones_usuario WHERE rol='PROFESOR' AND actor_id=:i FOR UPDATE WAIT 5",i=profesor_id)
                cur.fetchone()
                cur.execute('SELECT usuario,activo FROM profesores WHERE profesor_id=:i FOR UPDATE WAIT 5',i=profesor_id)
                perfil=cur.fetchone()
                correcto=perfil is not None and perfil[0].strip().lower()==usuario and perfil[1]==1
                if not correcto:cur.execute('ROLLBACK TO recuperar_clave')
                else:
                    cur.execute('UPDATE profesores SET contrasena=:h WHERE profesor_id=:i',h=bd.cifrar_contrasena(nueva_clave),i=profesor_id)
                    cur.execute("UPDATE sesiones_usuario SET revocada_en=SYSTIMESTAMP WHERE rol='PROFESOR' AND actor_id=:i",i=profesor_id)
                    cur.execute('DELETE FROM limites_acceso WHERE clave=:c',c=sha256(usuario.encode()).hexdigest())
                    cur.execute('DELETE FROM limites_acceso WHERE clave=:c',c=llave)
                    cur.execute("""INSERT INTO eventos_gestion(entidad,entidad_id,accion,motivo,actor_rol)
                        VALUES('PROFESOR',:i,'RESTABLECIMIENTO_CLAVE','Recuperacion con autorizacion docente privada','SISTEMA')""",i=profesor_id)
            if not correcto:
                cur.execute("""UPDATE limites_acceso SET intentos=:n,
                    ventana_en=CASE WHEN :exp=1 THEN SYSTIMESTAMP ELSE ventana_en END,
                    bloqueado_hasta=CASE WHEN :n>=5 THEN SYSTIMESTAMP+INTERVAL '15' MINUTE END WHERE clave=:c""",
                    n=intentos+1,exp=expirada,c=llave)
        conn.commit()
        return bool(correcto)
    return bd.ejecutar_con_reintentos(operacion,reintentos=1)
