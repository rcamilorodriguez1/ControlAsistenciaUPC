-- Demostracion PL/SQL inicial. El llamador controla COMMIT / ROLLBACK.
-- La app Python sigue usando bd.py; integrar el paquete es una fase posterior.
CREATE OR REPLACE PACKAGE pkg_asistencia AS
    FUNCTION porcentaje_asistencia(
        p_estudiante_id NUMBER, p_materia_id NUMBER DEFAULT NULL
    ) RETURN NUMBER;
    PROCEDURE matricular_estudiante(p_estudiante_id NUMBER, p_materia_id NUMBER);
    PROCEDURE registrar_asistencia(
        p_materia_id NUMBER, p_estudiante_id NUMBER,
        p_fecha_hora TIMESTAMP WITH TIME ZONE, p_presente NUMBER
    );
END pkg_asistencia;
/
SHOW ERRORS PACKAGE pkg_asistencia
CREATE OR REPLACE PACKAGE BODY pkg_asistencia AS
    FUNCTION porcentaje_asistencia(
        p_estudiante_id NUMBER, p_materia_id NUMBER DEFAULT NULL
    ) RETURN NUMBER IS
        v_porcentaje NUMBER;
    BEGIN
        SELECT NVL(ROUND(AVG(presente) * 100, 2), 0) INTO v_porcentaje
        FROM registros_asistencia
        WHERE estudiante_id = p_estudiante_id
          AND (p_materia_id IS NULL OR materia_id = p_materia_id);
        RETURN v_porcentaje;
    END;
    PROCEDURE matricular_estudiante(p_estudiante_id NUMBER, p_materia_id NUMBER) IS
    BEGIN
        INSERT INTO materia_estudiantes (estudiante_id, materia_id)
        VALUES (p_estudiante_id, p_materia_id);
    EXCEPTION
        WHEN DUP_VAL_ON_INDEX THEN
            RAISE_APPLICATION_ERROR(-20010, 'El estudiante ya esta matriculado en la materia.');
    END;
    PROCEDURE registrar_asistencia(
        p_materia_id NUMBER, p_estudiante_id NUMBER,
        p_fecha_hora TIMESTAMP WITH TIME ZONE, p_presente NUMBER
    ) IS
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
END pkg_asistencia;
/
SHOW ERRORS PACKAGE BODY pkg_asistencia
