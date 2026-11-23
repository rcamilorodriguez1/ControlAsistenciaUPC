-- Version 011: documento y codigo anterior conservado solo como legado.
CREATE OR REPLACE PACKAGE pkg_administracion AUTHID DEFINER AS
    PROCEDURE cuentas(p_tipo VARCHAR2,p_busqueda VARCHAR2,p_resultado OUT SYS_REFCURSOR);
    PROCEDURE listar_materias(p_busqueda VARCHAR2,p_resultado OUT SYS_REFCURSOR);
    PROCEDURE auditoria(p_tipo VARCHAR2,p_desde TIMESTAMP WITH TIME ZONE,p_hasta TIMESTAMP WITH TIME ZONE,
        p_limite NUMBER,p_resultado OUT SYS_REFCURSOR);
    PROCEDURE editar_profesor(p_id NUMBER,p_usuario VARCHAR2,p_nombre VARCHAR2,p_activo NUMBER,p_hash VARCHAR2,p_motivo VARCHAR2,p_version VARCHAR2);
    PROCEDURE editar_estudiante(p_id NUMBER,p_codigo VARCHAR2,p_nombre VARCHAR2,p_activo NUMBER,p_motivo VARCHAR2,p_version VARCHAR2);
    PROCEDURE editar_materia(p_id NUMBER,p_codigo VARCHAR2,p_nombre VARCHAR2,p_seccion VARCHAR2,p_profesor NUMBER,p_activo NUMBER,p_motivo VARCHAR2,p_version VARCHAR2);
    PROCEDURE registrar_exportacion(p_tipo VARCHAR2,p_cantidad NUMBER);
    PROCEDURE actualizar_documento(p_id NUMBER,p_huella VARCHAR2,p_tipo VARCHAR2,p_final VARCHAR2,p_version NUMBER);
END pkg_administracion;
/
CREATE OR REPLACE PACKAGE BODY pkg_administracion AS
    PROCEDURE exigir IS v_n NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_n FROM administradores WHERE administrador_id=pkg_auditoria.actor_actual AND activo=1;
        IF pkg_auditoria.rol_actual<>'ADMINISTRADOR' OR v_n<>1 THEN
            RAISE_APPLICATION_ERROR(-20101,'Se requiere una sesion administrativa activa.'); END IF;
    END;
    PROCEDURE texto(p_valor VARCHAR2,p_max NUMBER,p_opcional BOOLEAN DEFAULT FALSE) IS
    BEGIN
        IF (NOT p_opcional AND TRIM(p_valor) IS NULL) OR LENGTH(TRIM(p_valor))>p_max OR REGEXP_LIKE(p_valor,'[[:cntrl:]]') THEN
            RAISE_APPLICATION_ERROR(-20102,'Campo vacio, demasiado largo o con controles.'); END IF;
    END;
    PROCEDURE activo(p_activo NUMBER) IS
    BEGIN IF p_activo IS NULL OR p_activo NOT IN (0,1) THEN RAISE_APPLICATION_ERROR(-20102,'Estado de cuenta invalido.'); END IF; END;
    PROCEDURE codigo(p_valor VARCHAR2,p_max NUMBER) IS
    BEGIN
        texto(p_valor,p_max);
        IF NOT REGEXP_LIKE(UPPER(TRIM(p_valor)),'^[A-Z0-9][A-Z0-9_.-]*$') THEN RAISE_APPLICATION_ERROR(-20102,'Codigo o usuario invalido.'); END IF;
    END;
    PROCEDURE version_fila(p_actual NUMBER,p_version VARCHAR2) IS
    BEGIN
        IF p_version IS NULL OR TO_CHAR(p_actual,'TM9')<>p_version THEN
            RAISE_APPLICATION_ERROR(-20106,'El registro cambio desde que se cargo; vuelve a seleccionarlo antes de guardar.'); END IF;
    END;
    PROCEDURE evento(p_entidad VARCHAR2,p_id NUMBER,p_accion VARCHAR2,p_motivo VARCHAR2,p_antes CLOB DEFAULT NULL,p_despues CLOB DEFAULT NULL) IS
    BEGIN
        INSERT INTO eventos_gestion(entidad,entidad_id,accion,motivo,actor_rol,actor_id,valores_anteriores,valores_nuevos)
        VALUES(p_entidad,p_id,p_accion,TRIM(p_motivo),'ADMINISTRADOR',pkg_auditoria.actor_actual,p_antes,p_despues);
    END;
    PROCEDURE cuentas(p_tipo VARCHAR2,p_busqueda VARCHAR2,p_resultado OUT SYS_REFCURSOR) IS
    BEGIN
        exigir; texto(p_busqueda,100,TRUE);
        IF p_tipo='PROFESOR' THEN
            OPEN p_resultado FOR SELECT * FROM (SELECT profesor_id id,usuario,nombre,activo,creado_en,
                TO_CHAR(version_edicion,'TM9') version
                FROM profesores WHERE p_busqueda IS NULL OR LOWER(nombre||' '||usuario) LIKE '%'||LOWER(TRIM(p_busqueda))||'%' ORDER BY profesor_id) WHERE ROWNUM<=500;
        ELSIF p_tipo='ESTUDIANTE' THEN
            OPEN p_resultado FOR SELECT * FROM (SELECT e.estudiante_id id,e.codigo_institucional,e.nombre,e.activo,e.creado_en,v.tipo_documento,v.documento_final,NVL(v.version_credencial,0) version_documento,
                TO_CHAR(version_edicion,'TM9') version,
                CASE WHEN embedding_facial IS NULL THEN 0 ELSE 1 END tiene_rostro,
                CASE WHEN embedding_voz IS NULL THEN 0 ELSE 1 END tiene_voz
                FROM estudiantes e LEFT JOIN verificacion_estudiantes v ON v.estudiante_id=e.estudiante_id WHERE p_busqueda IS NULL OR LOWER(e.nombre||' '||v.documento_final) LIKE '%'||LOWER(TRIM(p_busqueda))||'%' ORDER BY e.estudiante_id) WHERE ROWNUM<=500;
        ELSE RAISE_APPLICATION_ERROR(-20102,'Tipo de cuenta no admitido.'); END IF;
    END;
    PROCEDURE listar_materias(p_busqueda VARCHAR2,p_resultado OUT SYS_REFCURSOR) IS
    BEGIN
        exigir; texto(p_busqueda,100,TRUE);
        OPEN p_resultado FOR SELECT * FROM (SELECT m.materia_id id,m.codigo_materia,m.nombre,m.seccion,m.profesor_id,
            p.nombre profesor,m.activo,TO_CHAR(m.version_edicion,'TM9') version,
            (SELECT COUNT(*) FROM clases c WHERE c.materia_id=m.materia_id) clases
            FROM materias m JOIN profesores p ON p.profesor_id=m.profesor_id
            WHERE p_busqueda IS NULL OR LOWER(m.nombre||' '||m.codigo_materia) LIKE '%'||LOWER(TRIM(p_busqueda))||'%'
            ORDER BY m.materia_id) WHERE ROWNUM<=500;
    END;
    PROCEDURE auditoria(p_tipo VARCHAR2,p_desde TIMESTAMP WITH TIME ZONE,p_hasta TIMESTAMP WITH TIME ZONE,p_limite NUMBER,p_resultado OUT SYS_REFCURSOR) IS
    BEGIN
        exigir;
        IF p_desde IS NULL OR p_hasta IS NULL OR p_hasta<=p_desde OR p_limite IS NULL OR p_limite<>TRUNC(p_limite) OR p_limite NOT BETWEEN 1 AND 10000 THEN
            RAISE_APPLICATION_ERROR(-20102,'Intervalo o limite de consulta invalido.'); END IF;
        IF p_tipo='ASISTENCIA' THEN
            OPEN p_resultado FOR SELECT * FROM (SELECT auditoria_id,operacion,asistencia_id,materia_anterior,estudiante_anterior,
                TO_CHAR(fecha_anterior,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') fecha_anterior,presente_anterior,materia_nueva,estudiante_nuevo,
                TO_CHAR(fecha_nueva,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') fecha_nueva,presente_nuevo,
                TO_CHAR(v.ocurrido_en,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') ocurrido_en,usuario_bd,actor_rol,actor_id,motivo,
                modulo,identificador_cliente,clase_anterior,clase_nueva,detectado_anterior,correccion_inicial,motivo_inicial,revisor_inicial,estado_anterior
                FROM v_auditoria_asistencia v WHERE v.ocurrido_en>=p_desde AND v.ocurrido_en<p_hasta ORDER BY v.ocurrido_en DESC,auditoria_id DESC) WHERE ROWNUM<=p_limite;
        ELSIF p_tipo='MATRICULAS' THEN
            OPEN p_resultado FOR SELECT * FROM (SELECT historial_id,accion,materia_id,estudiante_id,
                TO_CHAR(matriculado_en,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') matriculado_en,
                TO_CHAR(v.ocurrido_en,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') ocurrido_en,usuario_bd,actor_rol,actor_id,motivo,modulo,identificador_cliente
                FROM v_historial_matriculas v WHERE v.ocurrido_en>=p_desde AND v.ocurrido_en<p_hasta ORDER BY v.ocurrido_en DESC,historial_id DESC) WHERE ROWNUM<=p_limite;
        ELSIF p_tipo='GESTION' THEN
            OPEN p_resultado FOR SELECT * FROM (SELECT evento_id,entidad,entidad_id,accion,motivo,actor_rol,actor_id,
                TO_CHAR(v.ocurrido_en,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') ocurrido_en,valores_anteriores,valores_nuevos
                FROM v_eventos_gestion v WHERE v.ocurrido_en>=p_desde AND v.ocurrido_en<p_hasta ORDER BY v.ocurrido_en DESC,evento_id DESC) WHERE ROWNUM<=p_limite;
        ELSE RAISE_APPLICATION_ERROR(-20102,'Tipo de auditoria no admitido.'); END IF;
    END;
    PROCEDURE editar_profesor(p_id NUMBER,p_usuario VARCHAR2,p_nombre VARCHAR2,p_activo NUMBER,p_hash VARCHAR2,p_motivo VARCHAR2,p_version VARCHAR2) IS
        v profesores%ROWTYPE; v_antes CLOB; v_despues CLOB; v_m_antes CLOB; v_m_despues CLOB;
    BEGIN
        SAVEPOINT admin_profesor; exigir; codigo(p_usuario,100); texto(p_nombre,200); texto(p_motivo,500); activo(p_activo);
        IF p_hash IS NOT NULL AND NOT REGEXP_LIKE(p_hash,'^\$2[aby]\$[0-9]{2}\$[./A-Za-z0-9]{53}$','c') THEN
            RAISE_APPLICATION_ERROR(-20102,'El cambio de clave requiere un hash bcrypt valido.'); END IF;
        SELECT * INTO v FROM profesores WHERE profesor_id=p_id FOR UPDATE;
        version_fila(v.version_edicion,p_version);
        SELECT JSON_OBJECT('usuario' VALUE v.usuario,'nombre' VALUE v.nombre,'activo' VALUE v.activo) INTO v_antes FROM dual;
        UPDATE profesores SET usuario=LOWER(TRIM(p_usuario)),nombre=TRIM(p_nombre),activo=p_activo,contrasena=NVL(p_hash,contrasena) WHERE profesor_id=p_id;
        IF p_activo=0 THEN
            FOR m IN (SELECT materia_id,codigo_materia,nombre,seccion,profesor_id,activo FROM materias WHERE profesor_id=p_id AND activo=1 FOR UPDATE) LOOP
                SELECT JSON_OBJECT('codigo' VALUE m.codigo_materia,'nombre' VALUE m.nombre,'profesor_id' VALUE m.profesor_id,'activo' VALUE 1) INTO v_m_antes FROM dual;
                UPDATE materias SET activo=0 WHERE materia_id=m.materia_id;
                SELECT JSON_OBJECT('codigo' VALUE m.codigo_materia,'nombre' VALUE m.nombre,'profesor_id' VALUE m.profesor_id,'activo' VALUE 0) INTO v_m_despues FROM dual;
                evento('MATERIA',m.materia_id,'ARCHIVO_DOCENTE',p_motivo,v_m_antes,v_m_despues);
            END LOOP;
        END IF;
        SELECT JSON_OBJECT('usuario' VALUE LOWER(TRIM(p_usuario)),'nombre' VALUE TRIM(p_nombre),'activo' VALUE p_activo) INTO v_despues FROM dual;
        evento('PROFESOR',p_id,'EDICION_CUENTA',p_motivo,v_antes,v_despues);
        IF p_hash IS NOT NULL THEN evento('PROFESOR',p_id,'REINICIO_CLAVE',p_motivo); END IF;
    EXCEPTION WHEN OTHERS THEN ROLLBACK TO admin_profesor; RAISE;
    END;
    PROCEDURE editar_estudiante(p_id NUMBER,p_codigo VARCHAR2,p_nombre VARCHAR2,p_activo NUMBER,p_motivo VARCHAR2,p_version VARCHAR2) IS
        v estudiantes%ROWTYPE; v_antes CLOB; v_despues CLOB; v_motivo VARCHAR2(500):=pkg_auditoria.motivo_actual;
    BEGIN
        SAVEPOINT admin_estudiante; exigir; texto(p_nombre,200); texto(p_motivo,500); activo(p_activo);
        IF TRIM(p_codigo) IS NOT NULL THEN codigo(p_codigo,50); END IF;
        SELECT * INTO v FROM estudiantes WHERE estudiante_id=p_id FOR UPDATE;
        version_fila(v.version_edicion,p_version);
        SELECT JSON_OBJECT('codigo_institucional' VALUE v.codigo_institucional,'nombre' VALUE v.nombre,'activo' VALUE v.activo) INTO v_antes FROM dual;
        pkg_auditoria.fijar_motivo(p_motivo);
        IF p_activo=0 THEN DELETE FROM materia_estudiantes WHERE estudiante_id=p_id; END IF;
        UPDATE estudiantes SET codigo_institucional=NVL(UPPER(TRIM(p_codigo)),codigo_institucional),nombre=TRIM(p_nombre),activo=p_activo,
            embedding_facial=CASE WHEN p_activo=0 THEN NULL ELSE embedding_facial END,
            embedding_voz=CASE WHEN p_activo=0 THEN NULL ELSE embedding_voz END WHERE estudiante_id=p_id;
        SELECT JSON_OBJECT('codigo_institucional' VALUE NVL(UPPER(TRIM(p_codigo)),v.codigo_institucional),'nombre' VALUE TRIM(p_nombre),'activo' VALUE p_activo) INTO v_despues FROM dual;
        evento('ESTUDIANTE',p_id,'EDICION_CUENTA',p_motivo,v_antes,v_despues);
        pkg_auditoria.fijar_motivo(v_motivo);
    EXCEPTION WHEN OTHERS THEN ROLLBACK TO admin_estudiante; pkg_auditoria.fijar_motivo(v_motivo); RAISE;
    END;
    PROCEDURE editar_materia(p_id NUMBER,p_codigo VARCHAR2,p_nombre VARCHAR2,p_seccion VARCHAR2,p_profesor NUMBER,p_activo NUMBER,p_motivo VARCHAR2,p_version VARCHAR2) IS
        v materias%ROWTYPE; v_n NUMBER; v_antes CLOB; v_despues CLOB;
    BEGIN
        SAVEPOINT admin_materia; exigir; codigo(p_codigo,50); texto(p_nombre,200); texto(p_seccion,100,TRUE); texto(p_motivo,500); activo(p_activo);
        SELECT * INTO v FROM materias WHERE materia_id=p_id FOR UPDATE;
        version_fila(v.version_edicion,p_version);
        SELECT COUNT(*) INTO v_n FROM profesores WHERE profesor_id=p_profesor AND (p_activo=0 OR activo=1);
        IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20102,'Una materia activa requiere un profesor activo.'); END IF;
        IF p_profesor<>v.profesor_id THEN
            SELECT COUNT(*) INTO v_n FROM clases WHERE materia_id=p_id;
            IF v_n>0 THEN RAISE_APPLICATION_ERROR(-20103,'La materia tiene clases; conserva su docente para proteger la autoria historica.'); END IF;
        END IF;
        SELECT JSON_OBJECT('codigo' VALUE v.codigo_materia,'nombre' VALUE v.nombre,'seccion' VALUE v.seccion,'profesor_id' VALUE v.profesor_id,'activo' VALUE v.activo) INTO v_antes FROM dual;
        UPDATE materias SET codigo_materia=UPPER(TRIM(p_codigo)),nombre=TRIM(p_nombre),seccion=TRIM(p_seccion),profesor_id=p_profesor,activo=p_activo WHERE materia_id=p_id;
        SELECT JSON_OBJECT('codigo' VALUE UPPER(TRIM(p_codigo)),'nombre' VALUE TRIM(p_nombre),'seccion' VALUE TRIM(p_seccion),'profesor_id' VALUE p_profesor,'activo' VALUE p_activo) INTO v_despues FROM dual;
        evento('MATERIA',p_id,'EDICION_MATERIA',p_motivo,v_antes,v_despues);
    EXCEPTION WHEN OTHERS THEN ROLLBACK TO admin_materia; RAISE;
    END;
    PROCEDURE registrar_exportacion(p_tipo VARCHAR2,p_cantidad NUMBER) IS
    BEGIN
        exigir;
        IF p_tipo IS NULL OR p_tipo NOT IN ('ASISTENCIA','MATRICULAS','GESTION') OR p_cantidad IS NULL OR p_cantidad NOT BETWEEN 0 AND 10000 OR p_cantidad<>TRUNC(p_cantidad) THEN
            RAISE_APPLICATION_ERROR(-20102,'Exportacion invalida.'); END IF;
        evento('AUDITORIA',pkg_auditoria.actor_actual,'EXPORTACION_CSV','Preparacion de exportacion '||p_tipo||'; filas: '||p_cantidad);
    END;

    PROCEDURE actualizar_documento(p_id NUMBER,p_huella VARCHAR2,p_tipo VARCHAR2,p_final VARCHAR2,p_version NUMBER) IS
    BEGIN
        exigir;
        pkg_gestion.actualizar_documento(p_id,p_huella,p_tipo,p_final,p_version);
    END;
END pkg_administracion;
/
SHOW ERRORS PACKAGE BODY pkg_administracion
