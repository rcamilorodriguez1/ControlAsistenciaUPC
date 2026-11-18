CREATE OR REPLACE PACKAGE pkg_sesiones AUTHID DEFINER AS
    PROCEDURE abrir(p_rol VARCHAR2,p_actor NUMBER,p_hash VARCHAR2);
    PROCEDURE validar(p_rol VARCHAR2,p_actor NUMBER,p_hash VARCHAR2,p_renovar NUMBER DEFAULT 0);
    PROCEDURE cerrar(p_rol VARCHAR2,p_actor NUMBER,p_hash VARCHAR2);
END pkg_sesiones;
/
CREATE OR REPLACE PACKAGE BODY pkg_sesiones AS
    PROCEDURE parametros(p_rol VARCHAR2,p_actor NUMBER,p_hash VARCHAR2) IS
    BEGIN
        IF p_rol IS NULL OR p_rol NOT IN ('PROFESOR','ESTUDIANTE','ADMINISTRADOR') OR p_actor IS NULL OR p_actor<1 OR p_actor<>TRUNC(p_actor)
            OR p_hash IS NULL OR NOT REGEXP_LIKE(p_hash,'^[a-f0-9]{64}$','c') THEN
            RAISE_APPLICATION_ERROR(-20200,'Identidad de sesion invalida.'); END IF;
    END;
    PROCEDURE cuenta_activa(p_rol VARCHAR2,p_actor NUMBER) IS n NUMBER;
    BEGIN
        IF p_rol='PROFESOR' THEN SELECT COUNT(*) INTO n FROM profesores WHERE profesor_id=p_actor AND activo=1;
        ELSIF p_rol='ESTUDIANTE' THEN SELECT COUNT(*) INTO n FROM estudiantes WHERE estudiante_id=p_actor AND activo=1;
        ELSE SELECT COUNT(*) INTO n FROM administradores WHERE administrador_id=p_actor AND activo=1; END IF;
        IF n<>1 THEN RAISE_APPLICATION_ERROR(-20204,'La cuenta no esta activa.'); END IF;
    END;
    PROCEDURE abrir(p_rol VARCHAR2,p_actor NUMBER,p_hash VARCHAR2) IS
    BEGIN
        SAVEPOINT abrir_sesion;
        parametros(p_rol,p_actor,p_hash);
        -- La PK serializa tambien dos primeros accesos simultaneos a la misma cuenta.
        BEGIN
            INSERT INTO sesiones_usuario(rol,actor_id,token_hash,creada_en,actividad_en,expira_en)
            VALUES(p_rol,p_actor,p_hash,SYSTIMESTAMP,SYSTIMESTAMP,SYSTIMESTAMP+INTERVAL '8' HOUR);
        EXCEPTION WHEN DUP_VAL_ON_INDEX THEN
            UPDATE sesiones_usuario SET token_hash=p_hash,creada_en=SYSTIMESTAMP,actividad_en=SYSTIMESTAMP,
                expira_en=SYSTIMESTAMP+INTERVAL '8' HOUR,revocada_en=NULL
            WHERE rol=p_rol AND actor_id=p_actor;
        END;
        cuenta_activa(p_rol,p_actor);
    EXCEPTION WHEN OTHERS THEN ROLLBACK TO abrir_sesion; RAISE;
    END;
    PROCEDURE validar(p_rol VARCHAR2,p_actor NUMBER,p_hash VARCHAR2,p_renovar NUMBER DEFAULT 0) IS
        s sesiones_usuario%ROWTYPE; n NUMBER;
    BEGIN
        parametros(p_rol,p_actor,p_hash);
        IF p_renovar IS NULL OR p_renovar NOT IN (0,1) THEN RAISE_APPLICATION_ERROR(-20200,'Renovacion invalida.'); END IF;
        BEGIN
            SELECT * INTO s FROM sesiones_usuario WHERE rol=p_rol AND actor_id=p_actor FOR UPDATE WAIT 5;
        EXCEPTION WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20205,'La sesion no esta registrada.'); END;
        IF s.token_hash<>p_hash THEN RAISE_APPLICATION_ERROR(-20201,'La sesion fue reemplazada por otro acceso.'); END IF;
        IF s.revocada_en IS NOT NULL THEN RAISE_APPLICATION_ERROR(-20202,'La sesion ya fue cerrada.'); END IF;
        IF SYSTIMESTAMP>=s.expira_en OR SYSTIMESTAMP>=s.actividad_en+INTERVAL '30' MINUTE THEN
            RAISE_APPLICATION_ERROR(-20203,'La sesion caduco.'); END IF;
        cuenta_activa(p_rol,p_actor);
        IF p_rol='ESTUDIANTE' THEN
            -- SQL dinamico conserva la instalacion escalonada 007 -> 008.
            BEGIN
                EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM verificacion_estudiantes WHERE estudiante_id=:i
                    AND estado_verificacion=''EXCEPCIONAL'' AND (excepcion_activa=0 OR expira_en<=SYSTIMESTAMP)'
                    INTO n USING p_actor;
                IF n>0 THEN RAISE_APPLICATION_ERROR(-20206,'La autorizacion excepcional ya no esta vigente.'); END IF;
            EXCEPTION WHEN OTHERS THEN
                IF SQLCODE<>-942 THEN RAISE; END IF;
                SELECT COUNT(*) INTO n FROM versiones_esquema WHERE version='008';
                IF n>0 THEN RAISE_APPLICATION_ERROR(-20206,'No se pudo validar la autorizacion excepcional.'); END IF;
            END;
        END IF;
        IF p_renovar=1 THEN UPDATE sesiones_usuario SET actividad_en=SYSTIMESTAMP WHERE rol=p_rol AND actor_id=p_actor; END IF;
        -- El bloqueo dura hasta el COMMIT/ROLLBACK del llamador: un reemplazo espera a la operacion en curso.
    END;
    PROCEDURE cerrar(p_rol VARCHAR2,p_actor NUMBER,p_hash VARCHAR2) IS
    BEGIN
        parametros(p_rol,p_actor,p_hash);
        UPDATE sesiones_usuario SET revocada_en=SYSTIMESTAMP
        WHERE rol=p_rol AND actor_id=p_actor AND token_hash=p_hash AND revocada_en IS NULL;
        -- El logout de una pestaña reemplazada no cierra la nueva sesion.
    END;
END pkg_sesiones;
/
SHOW ERRORS PACKAGE BODY pkg_sesiones
