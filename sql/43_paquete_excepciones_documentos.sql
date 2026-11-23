-- Version 011: alta por documento y coincidencia con identidad registrada.
-- Version 009: la autorizacion administrativa puede sustituir una autorizacion docente.
-- Operaciones administrativas; NO ofrece un procedimiento para simular un acceso validado.
CREATE OR REPLACE PACKAGE pkg_excepciones AUTHID DEFINER AS
    PROCEDURE listar(p_busqueda VARCHAR2, p_salida OUT SYS_REFCURSOR);
    PROCEDURE autorizar(p_id IN OUT NUMBER, p_nombre VARCHAR2, p_codigo VARCHAR2,
        p_huella VARCHAR2, p_tipo VARCHAR2, p_final VARCHAR2, p_hash VARCHAR2,
        p_categoria VARCHAR2, p_referencia VARCHAR2, p_dias NUMBER, p_version NUMBER);
    PROCEDURE revocar(p_id NUMBER, p_version NUMBER, p_motivo VARCHAR2);
END pkg_excepciones;
/
CREATE OR REPLACE PACKAGE BODY pkg_excepciones AS
    PROCEDURE exigir IS n NUMBER;
    BEGIN
        SELECT COUNT(*) INTO n FROM administradores WHERE administrador_id=pkg_auditoria.actor_actual() AND activo=1;
        IF pkg_auditoria.rol_actual()<>'ADMINISTRADOR' OR n<>1 THEN
            RAISE_APPLICATION_ERROR(-20101,'Se requiere una cuenta administrativa activa.');
        END IF;
    END;

    PROCEDURE evento(p_id NUMBER,p_accion VARCHAR2,p_motivo VARCHAR2) IS
    BEGIN
        INSERT INTO eventos_gestion(entidad,entidad_id,accion,motivo,actor_rol,actor_id)
        VALUES('VERIFICACION',p_id,p_accion,p_motivo,'ADMINISTRADOR',pkg_auditoria.actor_actual());
    END;

    -- Mismo orden que el broker: SESION -> VERIFICACION -> CUENTA.
    PROCEDURE bloquear_sesion(p_id NUMBER) IS n NUMBER;
    BEGIN
        BEGIN
            INSERT INTO sesiones_usuario(rol,actor_id,token_hash,creada_en,actividad_en,expira_en,revocada_en)
            VALUES('ESTUDIANTE',p_id,RPAD('0',64,'0'),SYSTIMESTAMP,SYSTIMESTAMP,SYSTIMESTAMP+INTERVAL '8' HOUR,SYSTIMESTAMP);
        EXCEPTION WHEN DUP_VAL_ON_INDEX THEN NULL;
        END;
        SELECT actor_id INTO n FROM sesiones_usuario WHERE rol='ESTUDIANTE' AND actor_id=p_id FOR UPDATE WAIT 5;
        UPDATE sesiones_usuario SET revocada_en=SYSTIMESTAMP WHERE rol='ESTUDIANTE' AND actor_id=p_id;
    END;

    PROCEDURE listar(p_busqueda VARCHAR2,p_salida OUT SYS_REFCURSOR) IS
    BEGIN
        exigir;
        OPEN p_salida FOR
            SELECT e.estudiante_id,e.nombre,e.codigo_institucional,e.activo,
                NVL(v.estado_verificacion,'PENDIENTE') estado_verificacion,
                NVL(v.excepcion_activa,0) excepcion_activa,
                CASE WHEN v.excepcion_activa=1 AND (v.expira_en IS NULL OR v.expira_en>SYSTIMESTAMP) THEN 1 ELSE 0 END excepcion_vigente,
                v.tipo_documento,CASE WHEN v.documento_final IS NOT NULL THEN '****'||v.documento_final END documento,
                v.categoria,v.referencia,v.autorizado_por,v.autorizado_docente_por,v.materia_autorizacion_id,v.autorizado_en,v.expira_en,v.verificado_en,
                NVL(v.factores_verificados,0) factores_verificados,NVL(v.factores_requeridos,1) factores_requeridos,
                NVL(v.version_credencial,0) version_credencial,
                CASE WHEN e.embedding_facial IS NOT NULL THEN 1 ELSE 0 END tiene_rostro,
                CASE WHEN e.embedding_voz IS NOT NULL THEN 1 ELSE 0 END tiene_voz
            FROM estudiantes e LEFT JOIN verificacion_estudiantes v ON v.estudiante_id=e.estudiante_id
            WHERE p_busqueda IS NULL OR INSTR(UPPER(e.nombre),UPPER(p_busqueda))>0
                OR INSTR(UPPER(v.documento_final),UPPER(p_busqueda))>0
            ORDER BY e.estudiante_id;
    END;

    PROCEDURE autorizar(p_id IN OUT NUMBER,p_nombre VARCHAR2,p_codigo VARCHAR2,
        p_huella VARCHAR2,p_tipo VARCHAR2,p_final VARCHAR2,p_hash VARCHAR2,
        p_categoria VARCHAR2,p_referencia VARCHAR2,p_dias NUMBER,p_version NUMBER) IS
        v_version NUMBER; v_activo NUMBER; v_huella VARCHAR2(64);
    BEGIN
        exigir;
        IF p_huella IS NULL OR NOT REGEXP_LIKE(p_huella,'^[a-f0-9]{64}$','c') OR
           p_tipo IS NULL OR p_tipo NOT IN ('CC','TI','CE','PA') OR LENGTH(p_final)<>4 OR p_final IS NULL OR
           p_hash IS NULL OR NOT REGEXP_LIKE(p_hash,'^\$2[aby]\$[0-9]{2}\$[./A-Za-z0-9]{53}$','c') OR
           p_categoria IS NULL OR p_categoria NOT IN ('FISICA','MEDICA','TECNICA','ADMINISTRATIVA') OR
           TRIM(p_referencia) IS NULL OR LENGTH(p_referencia)>100 OR
           p_dias IS NULL OR p_dias<>TRUNC(p_dias) OR p_dias NOT BETWEEN 1 AND 365 OR p_version IS NULL THEN
            RAISE_APPLICATION_ERROR(-20301,'Autorizacion incompleta o no valida.');
        END IF;
        IF p_id IS NULL THEN
            IF TRIM(p_nombre) IS NULL OR LENGTH(p_nombre)>200 OR p_version<>0 THEN
                RAISE_APPLICATION_ERROR(-20301,'Nombre requerido para el alta por documento.');
            END IF;
            INSERT INTO estudiantes(nombre) VALUES(TRIM(p_nombre)) RETURNING estudiante_id INTO p_id;
        END IF;
        bloquear_sesion(p_id);
        BEGIN
            INSERT INTO verificacion_estudiantes(estudiante_id) VALUES(p_id);
        EXCEPTION WHEN DUP_VAL_ON_INDEX THEN NULL;
        END;
        SELECT version_credencial,documento_huella INTO v_version,v_huella FROM verificacion_estudiantes WHERE estudiante_id=p_id FOR UPDATE WAIT 5;
        SELECT activo INTO v_activo FROM estudiantes WHERE estudiante_id=p_id FOR UPDATE WAIT 5;
        IF v_activo<>1 THEN RAISE_APPLICATION_ERROR(-20302,'La cuenta debe estar activa.'); END IF;
        IF v_version<>p_version THEN RAISE_APPLICATION_ERROR(-20303,'El registro cambio. Actualiza la consulta.'); END IF;
        IF v_huella IS NOT NULL AND v_huella<>p_huella THEN RAISE_APPLICATION_ERROR(-20313,'El documento no coincide con el perfil. Actualizalo desde Cuentas.'); END IF;
        UPDATE verificacion_estudiantes SET documento_huella=p_huella,tipo_documento=p_tipo,documento_final=p_final,
            clave_hash=p_hash,excepcion_activa=1,categoria=p_categoria,referencia=TRIM(p_referencia),
            autorizado_por=pkg_auditoria.actor_actual(),autorizado_docente_por=NULL,materia_autorizacion_id=NULL,autorizado_en=SYSTIMESTAMP,
            expira_en=SYSTIMESTAMP+NUMTODSINTERVAL(p_dias,'DAY'),version_credencial=version_credencial+1
        WHERE estudiante_id=p_id;
        evento(p_id,'EXCEPCION_AUTORIZADA','Categoria: '||p_categoria||'; expediente: '||TRIM(p_referencia)||'; vigencia dias: '||p_dias);
    END;

    PROCEDURE revocar(p_id NUMBER,p_version NUMBER,p_motivo VARCHAR2) IS n NUMBER;
    BEGIN
        exigir;
        IF TRIM(p_motivo) IS NULL OR LENGTH(p_motivo)>450 OR p_version IS NULL THEN
            RAISE_APPLICATION_ERROR(-20301,'Indica el motivo administrativo de la revocacion.');
        END IF;
        bloquear_sesion(p_id);
        SELECT version_credencial INTO n FROM verificacion_estudiantes WHERE estudiante_id=p_id FOR UPDATE WAIT 5;
        IF n<>p_version THEN RAISE_APPLICATION_ERROR(-20303,'El registro cambio. Actualiza la consulta.'); END IF;
        UPDATE verificacion_estudiantes SET excepcion_activa=0,clave_hash=NULL,version_credencial=version_credencial+1
        WHERE estudiante_id=p_id;
        evento(p_id,'EXCEPCION_REVOCADA',TRIM(p_motivo));
    END;
END pkg_excepciones;
/
SHOW ERRORS
