-- Estado por sesion Oracle. Limpiarlo al adquirir y devolver conexiones al pool.
CREATE OR REPLACE PACKAGE pkg_auditoria AS
    PROCEDURE establecer_contexto(p_rol VARCHAR2, p_actor_id NUMBER DEFAULT NULL, p_motivo VARCHAR2 DEFAULT NULL);
    PROCEDURE limpiar_contexto;
    PROCEDURE fijar_motivo(p_motivo VARCHAR2);
    FUNCTION rol_actual RETURN VARCHAR2;
    FUNCTION actor_actual RETURN NUMBER;
    FUNCTION motivo_actual RETURN VARCHAR2;
END pkg_auditoria;
/
SHOW ERRORS PACKAGE pkg_auditoria
CREATE OR REPLACE PACKAGE BODY pkg_auditoria AS
    g_rol VARCHAR2(20);
    g_actor_id NUMBER;
    g_motivo auditoria_asistencia.motivo%TYPE;

    PROCEDURE fijar_motivo(p_motivo VARCHAR2) IS
    BEGIN
        IF LENGTH(TRIM(p_motivo)) > 500 THEN
            RAISE_APPLICATION_ERROR(-20060, 'El motivo admite hasta 500 caracteres.');
        END IF;
        g_motivo := TRIM(p_motivo);
    END;

    PROCEDURE establecer_contexto(p_rol VARCHAR2, p_actor_id NUMBER DEFAULT NULL, p_motivo VARCHAR2 DEFAULT NULL) IS
        v_rol VARCHAR2(20);
        v_existe NUMBER;
    BEGIN
        IF p_rol IS NULL OR UPPER(TRIM(p_rol)) NOT IN ('PROFESOR', 'ESTUDIANTE', 'SISTEMA') THEN
            RAISE_APPLICATION_ERROR(-20061, 'Rol de auditoria no valido.');
        END IF;
        v_rol := UPPER(TRIM(p_rol));
        IF v_rol = 'SISTEMA' THEN
            IF p_actor_id IS NOT NULL THEN
                RAISE_APPLICATION_ERROR(-20062, 'SISTEMA no admite actor_id.');
            END IF;
        ELSE
            IF p_actor_id IS NULL OR p_actor_id < 1 OR p_actor_id <> TRUNC(p_actor_id) THEN
                RAISE_APPLICATION_ERROR(-20063, 'El rol requiere un identificador positivo entero.');
            END IF;
            IF v_rol = 'PROFESOR' THEN
                SELECT COUNT(*) INTO v_existe FROM profesores WHERE profesor_id = p_actor_id;
            ELSE
                SELECT COUNT(*) INTO v_existe FROM estudiantes WHERE estudiante_id = p_actor_id;
            END IF;
            IF v_existe = 0 THEN
                RAISE_APPLICATION_ERROR(-20064, 'El actor declarado no existe.');
            END IF;
        END IF;
        fijar_motivo(p_motivo);
        g_rol := v_rol;
        g_actor_id := p_actor_id;
    END;

    PROCEDURE limpiar_contexto IS
    BEGIN
        g_rol := NULL;
        g_actor_id := NULL;
        g_motivo := NULL;
    END;
    FUNCTION rol_actual RETURN VARCHAR2 IS
    BEGIN RETURN NVL(g_rol, 'NO_IDENTIFICADO'); END;
    FUNCTION actor_actual RETURN NUMBER IS
    BEGIN RETURN g_actor_id; END;
    FUNCTION motivo_actual RETURN VARCHAR2 IS
    BEGIN RETURN g_motivo; END;
END pkg_auditoria;
/
SHOW ERRORS PACKAGE BODY pkg_auditoria
