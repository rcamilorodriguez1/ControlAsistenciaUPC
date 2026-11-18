-- Laboratorio PL/SQL transaccional: crea fixtures, muestra resultados y hace ROLLBACK.
-- Ejecutar desde una sesion de presentacion; no contiene DDL ni COMMIT.
SET SERVEROUTPUT ON
SET DEFINE OFF
SET AUTOCOMMIT OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE
    v_profesor profesores.profesor_id%TYPE;
    v_estudiante estudiantes.estudiante_id%TYPE;
    v_materia materias.materia_id%TYPE;
    v_asistencia registros_asistencia.asistencia_id%TYPE;
    v_codigo VARCHAR2(30) := 'DEMO_' || SUBSTR(RAWTOHEX(SYS_GUID()), 1, 16);
    v_cantidad NUMBER;
BEGIN
    SAVEPOINT inicio_demo_disparadores;
    pkg_auditoria.limpiar_contexto;
    INSERT INTO profesores (usuario, contrasena, nombre)
    VALUES (v_codigo, 'DEMO_NO_ES_UN_HASH_USABLE', 'Profesor de demostracion')
    RETURNING profesor_id INTO v_profesor;
    INSERT INTO estudiantes (nombre) VALUES ('Estudiante de demostracion')
    RETURNING estudiante_id INTO v_estudiante;
    INSERT INTO materias (codigo_materia, nombre, seccion, profesor_id)
    VALUES (v_codigo, 'Demostracion PL/SQL', 'DEMO', v_profesor)
    RETURNING materia_id INTO v_materia;

    pkg_auditoria.establecer_contexto('PROFESOR', v_profesor, 'Alta demostrativa');
    pkg_asistencia.matricular_estudiante(v_estudiante, v_materia);
    pkg_asistencia.registrar_asistencia(v_materia, v_estudiante, SYSTIMESTAMP, 0);
    SELECT asistencia_id INTO v_asistencia FROM registros_asistencia
    WHERE materia_id = v_materia AND estudiante_id = v_estudiante;

    -- El trigger impone SYSTIMESTAMP aunque se intente escribir una fecha antigua.
    UPDATE profesores SET actualizado_en = TIMESTAMP '2000-01-01 00:00:00' WHERE profesor_id = v_profesor;
    UPDATE estudiantes SET actualizado_en = TIMESTAMP '2000-01-01 00:00:00' WHERE estudiante_id = v_estudiante;
    UPDATE materias SET actualizado_en = TIMESTAMP '2000-01-01 00:00:00' WHERE materia_id = v_materia;
    SELECT COUNT(*) INTO v_cantidad FROM profesores
    WHERE profesor_id = v_profesor AND actualizado_en > SYSTIMESTAMP - INTERVAL '1' MINUTE;
    IF v_cantidad <> 1 THEN RAISE_APPLICATION_ERROR(-20070, 'Fallo el disparador de fecha.'); END IF;

    pkg_asistencia.corregir_asistencia(v_asistencia, 1, 'Correccion: evidencia revisada');
    UPDATE registros_asistencia SET presente = presente WHERE asistencia_id = v_asistencia;
    SELECT COUNT(*) INTO v_cantidad FROM auditoria_asistencia WHERE asistencia_id = v_asistencia;
    IF v_cantidad <> 1 THEN RAISE_APPLICATION_ERROR(-20071, 'Un UPDATE sin cambios no debe duplicar auditoria.'); END IF;
    pkg_asistencia.eliminar_asistencia(v_asistencia, 'Baja demostrativa autorizada');
    pkg_asistencia.retirar_estudiante(v_estudiante, v_materia, 'Retiro demostrativo');

    DBMS_OUTPUT.PUT_LINE('=== Asistencia: antes, despues y motivo ===');
    FOR r IN (SELECT operacion, presente_anterior, presente_nuevo, actor_rol, motivo
              FROM auditoria_asistencia WHERE asistencia_id = v_asistencia ORDER BY auditoria_id) LOOP
        DBMS_OUTPUT.PUT_LINE(r.operacion || ': ' || r.presente_anterior || ' -> '
            || NVL(TO_CHAR(r.presente_nuevo), 'NULL') || ' / ' || r.actor_rol || ' / ' || r.motivo);
    END LOOP;
    DBMS_OUTPUT.PUT_LINE('=== Matricula: alta y retiro ===');
    FOR r IN (SELECT accion, actor_rol, motivo FROM historial_matriculas
              WHERE materia_id = v_materia AND estudiante_id = v_estudiante ORDER BY historial_id) LOOP
        DBMS_OUTPUT.PUT_LINE(r.accion || ' / ' || r.actor_rol || ' / ' || r.motivo);
    END LOOP;
    SELECT COUNT(*) INTO v_cantidad FROM auditoria_asistencia WHERE asistencia_id = v_asistencia;
    IF v_cantidad <> 2 THEN RAISE_APPLICATION_ERROR(-20072, 'Se esperaban correccion y eliminacion auditadas.'); END IF;
    SELECT COUNT(*) INTO v_cantidad FROM historial_matriculas WHERE materia_id = v_materia;
    IF v_cantidad <> 2 THEN RAISE_APPLICATION_ERROR(-20073, 'Se esperaban alta y retiro.'); END IF;

    ROLLBACK TO inicio_demo_disparadores;
    pkg_auditoria.limpiar_contexto;
    SELECT COUNT(*) INTO v_cantidad FROM auditoria_asistencia WHERE asistencia_id = v_asistencia;
    IF v_cantidad <> 0 THEN RAISE_APPLICATION_ERROR(-20074, 'La auditoria debe revertirse con su transaccion.'); END IF;
    DBMS_OUTPUT.PUT_LINE('OK: cinco disparadores ejercitados; fixtures e historial revertidos.');
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK TO inicio_demo_disparadores;
        pkg_auditoria.limpiar_contexto;
        RAISE;
END;
/
