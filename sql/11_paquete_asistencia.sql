-- Version 002. Conserva las firmas de 001 y agrega operaciones auditables.
-- Sin COMMIT interno. El rol declarado no sustituye autenticacion de la app.
CREATE OR REPLACE PACKAGE pkg_asistencia AS
    FUNCTION porcentaje_asistencia(p_estudiante_id NUMBER, p_materia_id NUMBER DEFAULT NULL) RETURN NUMBER;
    PROCEDURE matricular_estudiante(p_estudiante_id NUMBER, p_materia_id NUMBER);
    PROCEDURE registrar_asistencia(p_materia_id NUMBER, p_estudiante_id NUMBER,
                                  p_fecha_hora TIMESTAMP WITH TIME ZONE, p_presente NUMBER);
    PROCEDURE corregir_asistencia(p_asistencia_id NUMBER, p_presente NUMBER, p_motivo VARCHAR2);
    PROCEDURE eliminar_asistencia(p_asistencia_id NUMBER, p_motivo VARCHAR2);
    PROCEDURE retirar_estudiante(p_estudiante_id NUMBER, p_materia_id NUMBER, p_motivo VARCHAR2 DEFAULT NULL);
END pkg_asistencia;
/
SHOW ERRORS PACKAGE pkg_asistencia
CREATE OR REPLACE PACKAGE BODY pkg_asistencia AS
    FUNCTION porcentaje_asistencia(p_estudiante_id NUMBER, p_materia_id NUMBER DEFAULT NULL) RETURN NUMBER IS
        v_porcentaje NUMBER;
    BEGIN
        SELECT NVL(ROUND(AVG(presente) * 100, 2), 0) INTO v_porcentaje
        FROM registros_asistencia
        WHERE estudiante_id = p_estudiante_id AND (p_materia_id IS NULL OR materia_id = p_materia_id);
        RETURN v_porcentaje;
    END;

    PROCEDURE matricular_estudiante(p_estudiante_id NUMBER, p_materia_id NUMBER) IS
    BEGIN
        INSERT INTO materia_estudiantes (estudiante_id, materia_id) VALUES (p_estudiante_id, p_materia_id);
    EXCEPTION
        WHEN DUP_VAL_ON_INDEX THEN RAISE_APPLICATION_ERROR(-20010, 'El estudiante ya esta matriculado en la materia.');
    END;

    PROCEDURE registrar_asistencia(p_materia_id NUMBER, p_estudiante_id NUMBER,
                                  p_fecha_hora TIMESTAMP WITH TIME ZONE, p_presente NUMBER) IS
        v_matricula NUMBER;
    BEGIN
        IF p_presente IS NULL OR p_presente NOT IN (0, 1) OR p_fecha_hora IS NULL THEN
            RAISE_APPLICATION_ERROR(-20011, 'Fecha obligatoria y presencia limitada a 0 o 1.');
        END IF;
        SELECT COUNT(*) INTO v_matricula FROM materia_estudiantes
        WHERE materia_id = p_materia_id AND estudiante_id = p_estudiante_id;
        IF v_matricula = 0 THEN
            RAISE_APPLICATION_ERROR(-20012, 'El estudiante no esta matriculado en la materia.');
        END IF;
        INSERT INTO registros_asistencia (materia_id, estudiante_id, fecha_hora, presente)
        VALUES (p_materia_id, p_estudiante_id, p_fecha_hora, p_presente);
    END;

    PROCEDURE exigir_motivo(p_motivo VARCHAR2) IS
    BEGIN
        IF TRIM(p_motivo) IS NULL OR LENGTH(TRIM(p_motivo)) > 500 THEN
            RAISE_APPLICATION_ERROR(-20030, 'Se requiere un motivo de 1 a 500 caracteres.');
        END IF;
    END;

    PROCEDURE bloquear_asistencia(p_asistencia_id NUMBER) IS
        v_profesor_id materias.profesor_id%TYPE;
    BEGIN
        IF pkg_auditoria.rol_actual <> 'PROFESOR' OR pkg_auditoria.actor_actual IS NULL THEN
            RAISE_APPLICATION_ERROR(-20031, 'Declare el contexto de un profesor antes de editar asistencia.');
        END IF;
        SELECT m.profesor_id INTO v_profesor_id
        FROM registros_asistencia ra JOIN materias m ON m.materia_id = ra.materia_id
        WHERE ra.asistencia_id = p_asistencia_id
        FOR UPDATE OF ra.presente;
        IF v_profesor_id <> pkg_auditoria.actor_actual THEN
            RAISE_APPLICATION_ERROR(-20032, 'La materia no pertenece al profesor declarado.');
        END IF;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20033, 'La asistencia no existe.');
    END;

    PROCEDURE corregir_asistencia(p_asistencia_id NUMBER, p_presente NUMBER, p_motivo VARCHAR2) IS
        v_motivo_anterior auditoria_asistencia.motivo%TYPE := pkg_auditoria.motivo_actual;
    BEGIN
        IF p_presente IS NULL OR p_presente NOT IN (0, 1) THEN
            RAISE_APPLICATION_ERROR(-20011, 'La presencia debe ser 0 o 1.');
        END IF;
        exigir_motivo(p_motivo);
        bloquear_asistencia(p_asistencia_id);
        pkg_auditoria.fijar_motivo(p_motivo);
        UPDATE registros_asistencia SET presente = p_presente WHERE asistencia_id = p_asistencia_id;
        pkg_auditoria.fijar_motivo(v_motivo_anterior);
    EXCEPTION
        WHEN OTHERS THEN
            pkg_auditoria.fijar_motivo(v_motivo_anterior);
            RAISE;
    END;

    PROCEDURE eliminar_asistencia(p_asistencia_id NUMBER, p_motivo VARCHAR2) IS
        v_motivo_anterior auditoria_asistencia.motivo%TYPE := pkg_auditoria.motivo_actual;
    BEGIN
        exigir_motivo(p_motivo);
        bloquear_asistencia(p_asistencia_id);
        pkg_auditoria.fijar_motivo(p_motivo);
        DELETE FROM registros_asistencia WHERE asistencia_id = p_asistencia_id;
        pkg_auditoria.fijar_motivo(v_motivo_anterior);
    EXCEPTION
        WHEN OTHERS THEN
            pkg_auditoria.fijar_motivo(v_motivo_anterior);
            RAISE;
    END;

    PROCEDURE retirar_estudiante(p_estudiante_id NUMBER, p_materia_id NUMBER, p_motivo VARCHAR2 DEFAULT NULL) IS
        v_permitido NUMBER := 0;
        v_motivo_anterior auditoria_asistencia.motivo%TYPE := pkg_auditoria.motivo_actual;
    BEGIN
        IF pkg_auditoria.rol_actual = 'ESTUDIANTE' AND pkg_auditoria.actor_actual = p_estudiante_id THEN
            v_permitido := 1;
        ELSIF pkg_auditoria.rol_actual = 'PROFESOR' THEN
            SELECT COUNT(*) INTO v_permitido FROM materias
            WHERE materia_id = p_materia_id AND profesor_id = pkg_auditoria.actor_actual;
        END IF;
        IF v_permitido = 0 THEN
            RAISE_APPLICATION_ERROR(-20034, 'El actor declarado no puede retirar esta matricula.');
        END IF;
        IF p_motivo IS NOT NULL THEN pkg_auditoria.fijar_motivo(p_motivo); END IF;
        DELETE FROM materia_estudiantes WHERE materia_id = p_materia_id AND estudiante_id = p_estudiante_id;
        IF SQL%ROWCOUNT = 0 THEN RAISE_APPLICATION_ERROR(-20035, 'La matricula no existe.'); END IF;
        pkg_auditoria.fijar_motivo(v_motivo_anterior);
    EXCEPTION
        WHEN OTHERS THEN
            pkg_auditoria.fijar_motivo(v_motivo_anterior);
            RAISE;
    END;
END pkg_asistencia;
/
SHOW ERRORS PACKAGE BODY pkg_asistencia
