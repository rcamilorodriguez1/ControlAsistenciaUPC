-- Preparacion reejecutable: conserva filas y no borra objetos.
DECLARE
    v_cantidad NUMBER;
    PROCEDURE crear_tabla(p_nombre VARCHAR2, p_ddl VARCHAR2) IS
        v_existe NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_existe FROM user_tables WHERE table_name = p_nombre;
        IF v_existe = 0 THEN EXECUTE IMMEDIATE p_ddl; END IF;
    END;
    PROCEDURE crear_indice(p_nombre VARCHAR2, p_ddl VARCHAR2) IS
        v_existe NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_existe FROM user_indexes WHERE index_name = p_nombre;
        IF v_existe = 0 THEN EXECUTE IMMEDIATE p_ddl; END IF;
    END;
    PROCEDURE agregar_actualizado(p_tabla VARCHAR2) IS
        v_existe NUMBER;
    BEGIN
        SELECT COUNT(*) INTO v_existe FROM user_tab_columns
        WHERE table_name = p_tabla AND column_name = 'ACTUALIZADO_EN';
        IF v_existe = 0 THEN
            EXECUTE IMMEDIATE 'ALTER TABLE ' || DBMS_ASSERT.SIMPLE_SQL_NAME(p_tabla)
                || ' ADD (actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL)';
        END IF;
    END;
BEGIN
    IF SYS_CONTEXT('USERENV', 'SESSION_USER') IN ('SYS', 'SYSTEM')
       OR SYS_CONTEXT('USERENV', 'CON_NAME') = 'CDB$ROOT' THEN
        RAISE_APPLICATION_ERROR(-20042, 'Ejecute la migracion como usuario de aplicacion en el PDB.');
    END IF;
    SELECT COUNT(*) INTO v_cantidad FROM versiones_esquema WHERE version = '001';
    IF v_cantidad <> 1 THEN
        RAISE_APPLICATION_ERROR(-20043, 'Se requiere la instalacion 001 antes de migrar.');
    END IF;
    SELECT COUNT(*) INTO v_cantidad FROM session_privs WHERE privilege = 'CREATE TRIGGER';
    IF v_cantidad = 0 THEN
        RAISE_APPLICATION_ERROR(-20044, 'Falta CREATE TRIGGER. El administrador debe ejecutar 00_habilitar_disparadores.sql.');
    END IF;
    crear_tabla('AUDITORIA_ASISTENCIA', q'~CREATE TABLE auditoria_asistencia (
        auditoria_id NUMBER GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_auditoria_asistencia PRIMARY KEY,
        operacion VARCHAR2(10 CHAR) NOT NULL,
        asistencia_id NUMBER NOT NULL,
        materia_anterior NUMBER NOT NULL,
        estudiante_anterior NUMBER NOT NULL,
        fecha_anterior TIMESTAMP WITH TIME ZONE NOT NULL,
        presente_anterior NUMBER(1) NOT NULL,
        materia_nueva NUMBER,
        estudiante_nuevo NUMBER,
        fecha_nueva TIMESTAMP WITH TIME ZONE,
        presente_nuevo NUMBER(1),
        ocurrido_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
        usuario_bd VARCHAR2(128 CHAR) NOT NULL,
        actor_rol VARCHAR2(20 CHAR) NOT NULL,
        actor_id NUMBER,
        motivo VARCHAR2(500 CHAR),
        modulo VARCHAR2(64 CHAR),
        identificador_cliente VARCHAR2(64 CHAR),
        CONSTRAINT ck_audasist_operacion CHECK (operacion IN ('UPDATE', 'DELETE')),
        CONSTRAINT ck_audasist_ant CHECK (presente_anterior IN (0, 1)),
        CONSTRAINT ck_audasist_nuevo CHECK (presente_nuevo IN (0, 1)),
        CONSTRAINT ck_audasist_rol CHECK (actor_rol IN ('PROFESOR', 'ESTUDIANTE', 'SISTEMA', 'NO_IDENTIFICADO'))
    )~');
    crear_tabla('HISTORIAL_MATRICULAS', q'~CREATE TABLE historial_matriculas (
        historial_id NUMBER GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_historial_matriculas PRIMARY KEY,
        accion VARCHAR2(10 CHAR) NOT NULL,
        materia_id NUMBER NOT NULL,
        estudiante_id NUMBER NOT NULL,
        matriculado_en TIMESTAMP WITH TIME ZONE NOT NULL,
        ocurrido_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
        usuario_bd VARCHAR2(128 CHAR) NOT NULL,
        actor_rol VARCHAR2(20 CHAR) NOT NULL,
        actor_id NUMBER,
        motivo VARCHAR2(500 CHAR),
        modulo VARCHAR2(64 CHAR),
        identificador_cliente VARCHAR2(64 CHAR),
        CONSTRAINT ck_histmat_accion CHECK (accion IN ('ALTA', 'RETIRO')),
        CONSTRAINT ck_histmat_rol CHECK (actor_rol IN ('PROFESOR', 'ESTUDIANTE', 'SISTEMA', 'NO_IDENTIFICADO'))
    )~');
    agregar_actualizado('PROFESORES');
    agregar_actualizado('ESTUDIANTES');
    agregar_actualizado('MATERIAS');
    crear_indice('IX_AUDASIST_REGISTRO', 'CREATE INDEX ix_audasist_registro ON auditoria_asistencia (asistencia_id, ocurrido_en)');
    crear_indice('IX_HISTMAT_MATERIA_ESTUDIANTE', 'CREATE INDEX ix_histmat_materia_estudiante ON historial_matriculas (materia_id, estudiante_id, ocurrido_en)');
END;
/
COMMENT ON TABLE auditoria_asistencia IS 'Instantaneas de correcciones y bajas; misma transaccion que la asistencia. Sin FK para conservar bajas en cascada.';
COMMENT ON TABLE historial_matriculas IS 'Eventos de alta y retiro posteriores a la migracion; no elimina historia al borrar entidades.';
COMMENT ON COLUMN auditoria_asistencia.actor_id IS 'Identidad declarada por la aplicacion o SQLPlus; no sustituye autenticacion.';
COMMENT ON COLUMN historial_matriculas.actor_id IS 'Identidad declarada por la aplicacion o SQLPlus; no sustituye autenticacion.';
COMMENT ON COLUMN profesores.actualizado_en IS 'Ultima sentencia UPDATE; las filas anteriores parten de la fecha de migracion.';
COMMENT ON COLUMN estudiantes.actualizado_en IS 'Ultima sentencia UPDATE; las filas anteriores parten de la fecha de migracion.';
COMMENT ON COLUMN materias.actualizado_en IS 'Ultima sentencia UPDATE; las filas anteriores parten de la fecha de migracion.';
