CREATE OR REPLACE PACKAGE pkg_gestion AS
    PROCEDURE crear_materia(p_codigo VARCHAR2,p_nombre VARCHAR2,p_seccion VARCHAR2,p_id OUT NUMBER);
    PROCEDURE matricular(p_estudiante NUMBER,p_materia NUMBER);
    PROCEDURE retirar(p_estudiante NUMBER,p_materia NUMBER,p_motivo VARCHAR2);
    PROCEDURE archivar_materia(p_materia NUMBER,p_motivo VARCHAR2);
    PROCEDURE retirar_biometria(p_estudiante NUMBER,p_motivo VARCHAR2);
    PROCEDURE archivar_estudiante(p_estudiante NUMBER,p_motivo VARCHAR2);
    PROCEDURE archivar_profesor(p_profesor NUMBER,p_motivo VARCHAR2);
END pkg_gestion;
/
CREATE OR REPLACE PACKAGE BODY pkg_gestion AS
    PROCEDURE motivo(p_valor VARCHAR2) IS
    BEGIN
        IF TRIM(p_valor) IS NULL OR LENGTH(TRIM(p_valor))>500 THEN RAISE_APPLICATION_ERROR(-20084,'Se requiere un motivo de 1 a 500 caracteres.'); END IF;
    END;
    PROCEDURE evento(p_tipo VARCHAR2,p_id NUMBER,p_accion VARCHAR2,p_motivo VARCHAR2) IS
    BEGIN
        motivo(p_motivo);
        INSERT INTO eventos_gestion(entidad,entidad_id,accion,motivo,actor_rol,actor_id)
        VALUES(p_tipo,p_id,p_accion,TRIM(p_motivo),pkg_auditoria.rol_actual,pkg_auditoria.actor_actual);
    END;
    PROCEDURE profesor IS v_n NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_n FROM profesores WHERE profesor_id=pkg_auditoria.actor_actual AND activo=1;
        IF pkg_auditoria.rol_actual<>'PROFESOR' OR v_n<>1 THEN RAISE_APPLICATION_ERROR(-20085,'Se requiere un profesor activo.'); END IF;
    END;
    PROCEDURE propietario(p_materia NUMBER) IS v_id NUMBER;
    BEGIN
        profesor;
        SELECT profesor_id INTO v_id FROM materias WHERE materia_id=p_materia FOR UPDATE;
        IF v_id<>pkg_auditoria.actor_actual THEN RAISE_APPLICATION_ERROR(-20085,'La materia no pertenece al profesor.'); END IF;
    EXCEPTION WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20085,'La materia no existe.'); END;
    PROCEDURE estudiante_propio(p_estudiante NUMBER) IS v_n NUMBER;
    BEGIN
        IF pkg_auditoria.rol_actual='SISTEMA' THEN RETURN; END IF;
        SELECT COUNT(*) INTO v_n FROM estudiantes WHERE estudiante_id=p_estudiante AND activo=1;
        IF pkg_auditoria.rol_actual<>'ESTUDIANTE' OR pkg_auditoria.actor_actual<>p_estudiante OR v_n<>1 THEN
            RAISE_APPLICATION_ERROR(-20085,'Se requiere la cuenta activa del estudiante.');
        END IF;
    END;
    PROCEDURE crear_materia(p_codigo VARCHAR2,p_nombre VARCHAR2,p_seccion VARCHAR2,p_id OUT NUMBER) IS
    BEGIN
        profesor;
        IF TRIM(p_codigo) IS NULL OR LENGTH(TRIM(p_codigo))>50 OR NOT REGEXP_LIKE(UPPER(TRIM(p_codigo)),'^[A-Z0-9][A-Z0-9_.-]*$')
           OR TRIM(p_nombre) IS NULL OR LENGTH(TRIM(p_nombre))>200 OR LENGTH(TRIM(p_seccion))>100 THEN
            RAISE_APPLICATION_ERROR(-20086,'Campos de materia invalidos.'); END IF;
        INSERT INTO materias(codigo_materia,nombre,seccion,profesor_id)
        VALUES(UPPER(TRIM(p_codigo)),TRIM(p_nombre),TRIM(p_seccion),pkg_auditoria.actor_actual) RETURNING materia_id INTO p_id;
    EXCEPTION WHEN DUP_VAL_ON_INDEX THEN RAISE_APPLICATION_ERROR(-20088,'El codigo de materia ya existe.'); END;
    PROCEDURE matricular(p_estudiante NUMBER,p_materia NUMBER) IS v_n NUMBER;
    BEGIN
        IF pkg_auditoria.rol_actual NOT IN ('PROFESOR','ESTUDIANTE') THEN RAISE_APPLICATION_ERROR(-20085,'Se requiere profesor o estudiante.'); END IF;
        IF pkg_auditoria.rol_actual='PROFESOR' THEN propietario(p_materia); ELSE estudiante_propio(p_estudiante); END IF;
        SELECT COUNT(*) INTO v_n FROM materias m JOIN profesores p ON p.profesor_id=m.profesor_id
        WHERE m.materia_id=p_materia AND m.activo=1 AND p.activo=1;
        IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20087,'La materia esta archivada o no existe.'); END IF;
        SELECT COUNT(*) INTO v_n FROM estudiantes WHERE estudiante_id=p_estudiante AND activo=1;
        IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20087,'El estudiante no esta activo.'); END IF;
        pkg_asistencia.matricular_estudiante(p_estudiante,p_materia);
    END;
    PROCEDURE retirar(p_estudiante NUMBER,p_materia NUMBER,p_motivo VARCHAR2) IS
    BEGIN
        IF pkg_auditoria.rol_actual NOT IN ('PROFESOR','ESTUDIANTE') THEN RAISE_APPLICATION_ERROR(-20085,'Se requiere profesor o estudiante.'); END IF;
        motivo(p_motivo);
        IF pkg_auditoria.rol_actual='PROFESOR' THEN propietario(p_materia); ELSE estudiante_propio(p_estudiante); END IF;
        pkg_asistencia.retirar_estudiante(p_estudiante,p_materia,TRIM(p_motivo));
    END;
    PROCEDURE archivar_materia(p_materia NUMBER,p_motivo VARCHAR2) IS
    BEGIN
        SAVEPOINT gestion_materia;
        motivo(p_motivo); propietario(p_materia);
        UPDATE materias SET activo=0 WHERE materia_id=p_materia AND activo=1;
        IF SQL%ROWCOUNT>0 THEN evento('MATERIA',p_materia,'ARCHIVO',p_motivo); END IF;
    EXCEPTION WHEN OTHERS THEN ROLLBACK TO gestion_materia; RAISE;
    END;
    PROCEDURE retirar_biometria(p_estudiante NUMBER,p_motivo VARCHAR2) IS
    BEGIN
        SAVEPOINT gestion_biometria;
        motivo(p_motivo); estudiante_propio(p_estudiante);
        UPDATE estudiantes SET embedding_facial=NULL,embedding_voz=NULL WHERE estudiante_id=p_estudiante;
        IF SQL%ROWCOUNT<>1 THEN RAISE_APPLICATION_ERROR(-20087,'El estudiante no existe.'); END IF;
        evento('ESTUDIANTE',p_estudiante,'RETIRADA_BIOMETRIA',p_motivo);
    EXCEPTION WHEN OTHERS THEN ROLLBACK TO gestion_biometria; RAISE;
    END;
    PROCEDURE archivar_estudiante(p_estudiante NUMBER,p_motivo VARCHAR2) IS
        v_motivo VARCHAR2(500):=pkg_auditoria.motivo_actual;
    BEGIN
        SAVEPOINT gestion_estudiante;
        motivo(p_motivo); estudiante_propio(p_estudiante);
        pkg_auditoria.fijar_motivo(p_motivo);
        DELETE FROM materia_estudiantes WHERE estudiante_id=p_estudiante;
        UPDATE estudiantes SET activo=0,embedding_facial=NULL,embedding_voz=NULL WHERE estudiante_id=p_estudiante;
        IF SQL%ROWCOUNT<>1 THEN RAISE_APPLICATION_ERROR(-20087,'El estudiante no existe.'); END IF;
        evento('ESTUDIANTE',p_estudiante,'ARCHIVO',p_motivo);
        pkg_auditoria.fijar_motivo(v_motivo);
    EXCEPTION WHEN OTHERS THEN ROLLBACK TO gestion_estudiante; pkg_auditoria.fijar_motivo(v_motivo); RAISE;
    END;
    PROCEDURE archivar_profesor(p_profesor NUMBER,p_motivo VARCHAR2) IS
    BEGIN
        SAVEPOINT gestion_profesor;
        motivo(p_motivo);
        IF pkg_auditoria.rol_actual<>'SISTEMA' THEN
            profesor;
            IF pkg_auditoria.actor_actual<>p_profesor THEN RAISE_APPLICATION_ERROR(-20085,'No puede archivar otra cuenta.'); END IF;
        END IF;
        UPDATE profesores SET activo=0 WHERE profesor_id=p_profesor;
        IF SQL%ROWCOUNT<>1 THEN RAISE_APPLICATION_ERROR(-20087,'El profesor no existe.'); END IF;
        UPDATE materias SET activo=0 WHERE profesor_id=p_profesor;
        evento('PROFESOR',p_profesor,'ARCHIVO',p_motivo);
    EXCEPTION WHEN OTHERS THEN ROLLBACK TO gestion_profesor; RAISE;
    END;
END pkg_gestion;
/
SHOW ERRORS PACKAGE BODY pkg_gestion
