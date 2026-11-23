-- Version 011: registro y mantenimiento por documento.
CREATE OR REPLACE PACKAGE pkg_gestion AS
    PROCEDURE crear_materia(p_codigo VARCHAR2,p_nombre VARCHAR2,p_seccion VARCHAR2,p_id OUT NUMBER);
    PROCEDURE matricular(p_estudiante NUMBER,p_materia NUMBER);
    PROCEDURE retirar(p_estudiante NUMBER,p_materia NUMBER,p_motivo VARCHAR2);
    PROCEDURE archivar_materia(p_materia NUMBER,p_motivo VARCHAR2);
    PROCEDURE retirar_biometria(p_estudiante NUMBER,p_motivo VARCHAR2);
    PROCEDURE archivar_estudiante(p_estudiante NUMBER,p_motivo VARCHAR2);
    PROCEDURE archivar_profesor(p_profesor NUMBER,p_motivo VARCHAR2);
    PROCEDURE registrar_estudiante(p_nombre VARCHAR2,p_huella VARCHAR2,p_tipo VARCHAR2,p_final VARCHAR2,
        p_facial CLOB,p_voz CLOB,p_id OUT NUMBER);
    PROCEDURE actualizar_documento(p_id NUMBER,p_huella VARCHAR2,p_tipo VARCHAR2,p_final VARCHAR2,p_version NUMBER);
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

    PROCEDURE documento_valido(p_huella VARCHAR2,p_tipo VARCHAR2,p_final VARCHAR2) IS
    BEGIN
        IF p_huella IS NULL OR NOT REGEXP_LIKE(p_huella,'^[a-f0-9]{64}$','c') OR
           p_tipo IS NULL OR p_tipo NOT IN ('CC','TI','CE','PA') OR p_final IS NULL OR LENGTH(p_final)<>4 THEN
            RAISE_APPLICATION_ERROR(-20313,'Documento no valido.');
        END IF;
    END;
    PROCEDURE registrar_estudiante(p_nombre VARCHAR2,p_huella VARCHAR2,p_tipo VARCHAR2,p_final VARCHAR2,
        p_facial CLOB,p_voz CLOB,p_id OUT NUMBER) IS
    BEGIN
        SAVEPOINT registro_documento_011;
        documento_valido(p_huella,p_tipo,p_final);
        IF TRIM(p_nombre) IS NULL OR LENGTH(p_nombre)>200 OR p_facial IS NULL THEN
            RAISE_APPLICATION_ERROR(-20313,'Nombre y muestra facial obligatorios para el alta publica.');
        END IF;
        INSERT INTO estudiantes(nombre,embedding_facial,embedding_voz)
        VALUES(TRIM(p_nombre),p_facial,p_voz) RETURNING estudiante_id INTO p_id;
        INSERT INTO verificacion_estudiantes(estudiante_id,documento_huella,tipo_documento,documento_final)
        VALUES(p_id,p_huella,p_tipo,p_final);
        INSERT INTO eventos_gestion(entidad,entidad_id,accion,motivo,actor_rol)
        VALUES('ESTUDIANTE',p_id,'ALTA_DOCUMENTO','Alta publica con documento registrado y muestra facial.','SISTEMA');
    EXCEPTION WHEN OTHERS THEN ROLLBACK TO registro_documento_011; RAISE;
    END;
    PROCEDURE actualizar_documento(p_id NUMBER,p_huella VARCHAR2,p_tipo VARCHAR2,p_final VARCHAR2,p_version NUMBER) IS
        n NUMBER; v_version NUMBER; v_huella VARCHAR2(64); v_tipo VARCHAR2(2); v_final VARCHAR2(4);
        v_rol VARCHAR2(20):=pkg_auditoria.rol_actual;
    BEGIN
        SAVEPOINT documento_011;
        documento_valido(p_huella,p_tipo,p_final);
        IF v_rol='ESTUDIANTE' THEN
            IF pkg_auditoria.actor_actual IS NULL OR pkg_auditoria.actor_actual<>p_id THEN RAISE_APPLICATION_ERROR(-20085,'Solo puede editar su documento.'); END IF;
        ELSIF v_rol='ADMINISTRADOR' THEN
            SELECT COUNT(*) INTO n FROM administradores WHERE administrador_id=pkg_auditoria.actor_actual AND activo=1;
            IF n<>1 THEN RAISE_APPLICATION_ERROR(-20085,'Se requiere administrador activo.'); END IF;
        ELSE RAISE_APPLICATION_ERROR(-20085,'No puede editar documentos.'); END IF;
        -- Mismo orden de bloqueo del acceso y de las excepciones: sesion -> verificacion -> cuenta.
        BEGIN
            INSERT INTO sesiones_usuario(rol,actor_id,token_hash,creada_en,actividad_en,expira_en,revocada_en)
            VALUES('ESTUDIANTE',p_id,RPAD('0',64,'0'),SYSTIMESTAMP,SYSTIMESTAMP,SYSTIMESTAMP+INTERVAL '8' HOUR,SYSTIMESTAMP);
        EXCEPTION WHEN DUP_VAL_ON_INDEX THEN NULL; END;
        SELECT actor_id INTO n FROM sesiones_usuario WHERE rol='ESTUDIANTE' AND actor_id=p_id FOR UPDATE WAIT 5;
        BEGIN INSERT INTO verificacion_estudiantes(estudiante_id) VALUES(p_id);
        EXCEPTION WHEN DUP_VAL_ON_INDEX THEN NULL; END;
        SELECT version_credencial,documento_huella,tipo_documento,documento_final INTO v_version,v_huella,v_tipo,v_final
            FROM verificacion_estudiantes WHERE estudiante_id=p_id FOR UPDATE WAIT 5;
        IF p_version IS NULL OR p_version<>v_version THEN RAISE_APPLICATION_ERROR(-20303,'El documento cambio. Recarga el perfil.'); END IF;
        SELECT activo INTO n FROM estudiantes WHERE estudiante_id=p_id FOR UPDATE WAIT 5;
        IF n<>1 THEN RAISE_APPLICATION_ERROR(-20313,'La cuenta debe estar activa.'); END IF;
        IF v_huella=p_huella AND v_tipo=p_tipo AND v_final=p_final THEN RETURN; END IF;
        UPDATE verificacion_estudiantes SET documento_huella=p_huella,tipo_documento=p_tipo,documento_final=p_final,
            excepcion_activa=0,clave_hash=NULL,version_credencial=version_credencial+1 WHERE estudiante_id=p_id;
        UPDATE sesiones_usuario SET revocada_en=SYSTIMESTAMP WHERE rol='ESTUDIANTE' AND actor_id=p_id;
        INSERT INTO eventos_gestion(entidad,entidad_id,accion,motivo,actor_rol,actor_id)
        VALUES('ESTUDIANTE',p_id,'DOCUMENTO_ACTUALIZADO','Documento actualizado; sesiones y autorizacion anterior invalidadas.',v_rol,pkg_auditoria.actor_actual);
    EXCEPTION WHEN OTHERS THEN ROLLBACK TO documento_011; RAISE;
    END;
END pkg_gestion;
/
SHOW ERRORS PACKAGE BODY pkg_gestion
