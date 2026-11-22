SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
SET SERVEROUTPUT ON
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE
    v_n NUMBER;
    PROCEDURE columna(p_nombre VARCHAR2) IS
    BEGIN
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='EVENTOS_GESTION' AND column_name=p_nombre;
        IF v_n=0 THEN EXECUTE IMMEDIATE 'ALTER TABLE eventos_gestion ADD ('||p_nombre||' CLOB)'; END IF;
    END;
    PROCEDURE rol(p_tabla VARCHAR2,p_nombre VARCHAR2) IS
    BEGIN
        SELECT COUNT(*) INTO v_n FROM user_constraints WHERE constraint_name=p_nombre;
        IF v_n>0 THEN EXECUTE IMMEDIATE 'ALTER TABLE '||p_tabla||' DROP CONSTRAINT '||p_nombre; END IF;
        EXECUTE IMMEDIATE 'ALTER TABLE '||p_tabla||' ADD CONSTRAINT '||p_nombre||
            ' CHECK(actor_rol IN (''PROFESOR'',''ESTUDIANTE'',''ADMINISTRADOR'',''SISTEMA'',''NO_IDENTIFICADO''))';
    END;
    PROCEDURE version_edicion(p_tabla VARCHAR2) IS
    BEGIN
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name=p_tabla AND column_name='VERSION_EDICION';
        IF v_n=0 THEN EXECUTE IMMEDIATE 'ALTER TABLE '||p_tabla||' ADD (version_edicion NUMBER DEFAULT 0 NOT NULL)'; END IF;
    END;
BEGIN
    SELECT COUNT(*) INTO v_n FROM versiones_esquema WHERE version='005';
    IF v_n<>1 OR SYS_CONTEXT('USERENV','SESSION_USER') IN ('SYS','SYSTEM') THEN
        RAISE_APPLICATION_ERROR(-20100,'Se requiere 005 y el usuario del proyecto.'); END IF;
    SELECT COUNT(*) INTO v_n FROM user_tables WHERE table_name='ADMINISTRADORES';
    IF v_n=0 THEN EXECUTE IMMEDIATE q'~CREATE TABLE administradores (
        administrador_id NUMBER GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_administradores PRIMARY KEY,
        usuario VARCHAR2(100 CHAR) NOT NULL, nombre VARCHAR2(200 CHAR) NOT NULL,
        contrasena VARCHAR2(255 CHAR) NOT NULL, activo NUMBER(1) DEFAULT 1 NOT NULL,
        creado_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
        actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
        CONSTRAINT ck_administradores_activo CHECK(activo IN (0,1)))~'; END IF;
    SELECT COUNT(*) INTO v_n FROM user_indexes WHERE index_name='UQ_ADMINISTRADORES_USUARIO';
    IF v_n=0 THEN EXECUTE IMMEDIATE 'CREATE UNIQUE INDEX uq_administradores_usuario ON administradores(LOWER(TRIM(usuario)))'; END IF;
    columna('VALORES_ANTERIORES'); columna('VALORES_NUEVOS');
    version_edicion('PROFESORES'); version_edicion('ESTUDIANTES'); version_edicion('MATERIAS');
    SELECT COUNT(*) INTO v_n FROM user_constraints WHERE constraint_name='CK_EVENTOS_ANTES_JSON';
    IF v_n=0 THEN EXECUTE IMMEDIATE 'ALTER TABLE eventos_gestion ADD CONSTRAINT ck_eventos_antes_json CHECK(valores_anteriores IS JSON)'; END IF;
    SELECT COUNT(*) INTO v_n FROM user_constraints WHERE constraint_name='CK_EVENTOS_DESPUES_JSON';
    IF v_n=0 THEN EXECUTE IMMEDIATE 'ALTER TABLE eventos_gestion ADD CONSTRAINT ck_eventos_despues_json CHECK(valores_nuevos IS JSON)'; END IF;
    rol('AUDITORIA_ASISTENCIA','CK_AUDASIST_ROL');
    rol('HISTORIAL_MATRICULAS','CK_HISTMAT_ROL');
END;
/
CREATE OR REPLACE TRIGGER trg_administradores_actualizado
BEFORE UPDATE ON administradores FOR EACH ROW
BEGIN :NEW.actualizado_en:=SYSTIMESTAMP; END;
/
CREATE OR REPLACE VIEW v_eventos_gestion AS
SELECT evento_id,entidad,entidad_id,accion,motivo,actor_rol,actor_id,ocurrido_en,
       valores_anteriores,valores_nuevos FROM eventos_gestion;
@sql/27_contexto_administrativo.sql
@sql/31_versiones_edicion.sql
@sql/28_paquete_administracion.sql
@sql/36_recompilar_esquema.sql
@sql/04_verificar.sql
COMMENT ON TABLE administradores IS 'Administradores de aplicacion; alta privada, clave bcrypt y sin registro publico.';
COMMENT ON COLUMN eventos_gestion.valores_anteriores IS 'Instantanea JSON administrativa sin hashes ni biometria.';
INSERT INTO versiones_esquema(version,descripcion)
SELECT '006','Administracion institucional, permisos, edicion auditable y exportacion' FROM dual
WHERE NOT EXISTS(SELECT 1 FROM versiones_esquema WHERE version='006');
COMMIT;
PROMPT Administracion 006 instalada sin borrar cuentas, materias ni historia.
