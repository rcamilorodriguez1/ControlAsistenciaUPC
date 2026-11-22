-- Acceso exclusivamente por la cuenta tecnica limitada; sin DML directo al runtime.
CREATE OR REPLACE PACKAGE pkg_excepciones_docentes AUTHID DEFINER AS
    PROCEDURE listar(p_materia NUMBER,p_salida OUT SYS_REFCURSOR);
    PROCEDURE autorizar(p_materia NUMBER,p_id NUMBER,p_huella VARCHAR2,p_tipo VARCHAR2,p_final VARCHAR2,
        p_hash VARCHAR2,p_categoria VARCHAR2,p_referencia VARCHAR2,p_dias NUMBER,p_version NUMBER);
    PROCEDURE revocar(p_materia NUMBER,p_id NUMBER,p_version NUMBER,p_motivo VARCHAR2);
END pkg_excepciones_docentes;
/
CREATE OR REPLACE PACKAGE BODY pkg_excepciones_docentes AS
    PROCEDURE exigir(p_materia NUMBER) IS n NUMBER;
    BEGIN
        IF NVL(pkg_auditoria.rol_actual(),'ANONIMO')<>'PROFESOR' THEN
            RAISE_APPLICATION_ERROR(-20311,'Se requiere una sesion docente activa.');
        END IF;
        SELECT COUNT(*) INTO n FROM profesores p JOIN materias m ON m.profesor_id=p.profesor_id
        WHERE p.profesor_id=pkg_auditoria.actor_actual() AND p.activo=1 AND m.materia_id=p_materia AND m.activo=1;
        IF n<>1 THEN RAISE_APPLICATION_ERROR(-20311,'La materia no pertenece al docente activo.'); END IF;
    END;

    PROCEDURE bloquear(p_materia NUMBER,p_id NUMBER,p_version NUMBER,p_revocar BOOLEAN) IS
        n NUMBER; v_admin NUMBER; v_docente NUMBER;
    BEGIN
        exigir(p_materia);
        -- Orden: materia -> matricula -> sesion del alumno -> verificacion -> cuenta.
        SELECT materia_id INTO n FROM materias WHERE materia_id=p_materia
            AND profesor_id=pkg_auditoria.actor_actual() AND activo=1 FOR UPDATE WAIT 5;
        SELECT estudiante_id INTO n FROM materia_estudiantes WHERE materia_id=p_materia
            AND estudiante_id=p_id FOR UPDATE WAIT 5;
        BEGIN
            INSERT INTO sesiones_usuario(rol,actor_id,token_hash,creada_en,actividad_en,expira_en,revocada_en)
            VALUES('ESTUDIANTE',p_id,RPAD('0',64,'0'),SYSTIMESTAMP,SYSTIMESTAMP,SYSTIMESTAMP+INTERVAL '8' HOUR,SYSTIMESTAMP);
        EXCEPTION WHEN DUP_VAL_ON_INDEX THEN NULL;
        END;
        SELECT actor_id INTO n FROM sesiones_usuario WHERE rol='ESTUDIANTE' AND actor_id=p_id FOR UPDATE WAIT 5;
        BEGIN
            INSERT INTO verificacion_estudiantes(estudiante_id) VALUES(p_id);
        EXCEPTION WHEN DUP_VAL_ON_INDEX THEN NULL;
        END;
        SELECT version_credencial,autorizado_por,autorizado_docente_por INTO n,v_admin,v_docente
            FROM verificacion_estudiantes WHERE estudiante_id=p_id FOR UPDATE WAIT 5;
        IF p_version IS NULL OR n<>p_version THEN RAISE_APPLICATION_ERROR(-20303,'El registro cambio. Actualiza la consulta.'); END IF;
        IF v_admin IS NOT NULL OR (v_docente IS NOT NULL AND v_docente<>pkg_auditoria.actor_actual()) OR
           (p_revocar AND v_docente IS NULL) THEN
            RAISE_APPLICATION_ERROR(-20311,'Solo puedes gestionar las autorizaciones que emitiste. Solicita revision administrativa.');
        END IF;
        SELECT activo INTO n FROM estudiantes WHERE estudiante_id=p_id FOR UPDATE WAIT 5;
        IF n<>1 THEN RAISE_APPLICATION_ERROR(-20302,'La cuenta del estudiante debe estar activa.'); END IF;
        UPDATE sesiones_usuario SET revocada_en=SYSTIMESTAMP WHERE rol='ESTUDIANTE' AND actor_id=p_id;
    EXCEPTION WHEN NO_DATA_FOUND THEN
        RAISE_APPLICATION_ERROR(-20311,'El estudiante debe estar matriculado en tu materia activa.');
    END;

    PROCEDURE evento(p_id NUMBER,p_accion VARCHAR2,p_motivo VARCHAR2) IS
    BEGIN
        INSERT INTO eventos_gestion(entidad,entidad_id,accion,motivo,actor_rol,actor_id)
        VALUES('VERIFICACION',p_id,p_accion,p_motivo,'PROFESOR',pkg_auditoria.actor_actual());
    END;

    PROCEDURE listar(p_materia NUMBER,p_salida OUT SYS_REFCURSOR) IS
    BEGIN
        exigir(p_materia);
        OPEN p_salida FOR
            SELECT e.estudiante_id,e.nombre,e.codigo_institucional,
                NVL(v.excepcion_activa,0) excepcion_activa,
                CASE WHEN v.excepcion_activa=1 AND v.expira_en>SYSTIMESTAMP THEN 1 ELSE 0 END excepcion_vigente,
                v.expira_en,NVL(v.version_credencial,0) version_credencial,
                CASE WHEN v.autorizado_por IS NULL AND (v.autorizado_docente_por IS NULL OR
                    v.autorizado_docente_por=pkg_auditoria.actor_actual()) THEN 1 ELSE 0 END puede_autorizar,
                CASE WHEN v.autorizado_docente_por=pkg_auditoria.actor_actual() AND v.excepcion_activa=1 THEN 1 ELSE 0 END puede_revocar
            FROM estudiantes e JOIN materia_estudiantes me ON me.estudiante_id=e.estudiante_id
            LEFT JOIN verificacion_estudiantes v ON v.estudiante_id=e.estudiante_id
            WHERE me.materia_id=p_materia AND e.activo=1 ORDER BY e.nombre,e.estudiante_id;
    END;

    PROCEDURE autorizar(p_materia NUMBER,p_id NUMBER,p_huella VARCHAR2,p_tipo VARCHAR2,p_final VARCHAR2,
        p_hash VARCHAR2,p_categoria VARCHAR2,p_referencia VARCHAR2,p_dias NUMBER,p_version NUMBER) IS
    BEGIN
        exigir(p_materia);
        IF p_huella IS NULL OR NOT REGEXP_LIKE(p_huella,'^[a-f0-9]{64}$','c') OR
           p_tipo IS NULL OR p_tipo NOT IN ('CC','TI','CE','PA') OR p_final IS NULL OR LENGTH(p_final)<>4 OR
           p_hash IS NULL OR NOT REGEXP_LIKE(p_hash,'^\$2[aby]\$[0-9]{2}\$[./A-Za-z0-9]{53}$','c') OR
           p_categoria IS NULL OR p_categoria NOT IN ('FISICA','MEDICA','TECNICA','ADMINISTRATIVA') OR
           TRIM(p_referencia) IS NULL OR LENGTH(p_referencia)>100 OR p_dias IS NULL OR
           p_dias<>TRUNC(p_dias) OR p_dias NOT BETWEEN 1 AND 365 THEN
            RAISE_APPLICATION_ERROR(-20301,'Autorizacion incompleta o no valida.');
        END IF;
        bloquear(p_materia,p_id,p_version,FALSE);
        UPDATE verificacion_estudiantes SET documento_huella=p_huella,tipo_documento=p_tipo,documento_final=p_final,
            clave_hash=p_hash,excepcion_activa=1,categoria=p_categoria,referencia=TRIM(p_referencia),
            autorizado_por=NULL,autorizado_docente_por=pkg_auditoria.actor_actual(),materia_autorizacion_id=p_materia,
            autorizado_en=SYSTIMESTAMP,expira_en=SYSTIMESTAMP+NUMTODSINTERVAL(p_dias,'DAY'),
            version_credencial=version_credencial+1 WHERE estudiante_id=p_id;
        evento(p_id,'EXCEPCION_AUTORIZADA','Materia: '||p_materia||'; categoria: '||p_categoria||'; vigencia dias: '||p_dias);
    END;

    PROCEDURE revocar(p_materia NUMBER,p_id NUMBER,p_version NUMBER,p_motivo VARCHAR2) IS
    BEGIN
        IF TRIM(p_motivo) IS NULL OR LENGTH(p_motivo)>450 THEN
            RAISE_APPLICATION_ERROR(-20301,'Indica el motivo de la revocacion.');
        END IF;
        bloquear(p_materia,p_id,p_version,TRUE);
        UPDATE verificacion_estudiantes SET excepcion_activa=0,clave_hash=NULL,
            version_credencial=version_credencial+1 WHERE estudiante_id=p_id;
        evento(p_id,'EXCEPCION_REVOCADA',TRIM(p_motivo));
    END;
END pkg_excepciones_docentes;
/
SHOW ERRORS
