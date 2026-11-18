SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
SET SERVEROUTPUT ON
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE
    v_n NUMBER;
    PROCEDURE agregar(p_tabla VARCHAR2,p_col VARCHAR2,p_ddl VARCHAR2) IS
    BEGIN
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name=p_tabla AND column_name=p_col;
        IF v_n=0 THEN EXECUTE IMMEDIATE 'ALTER TABLE '||p_tabla||' ADD ('||p_ddl||')'; END IF;
    END;
BEGIN
    SELECT COUNT(*) INTO v_n FROM versiones_esquema WHERE version='006';
    IF v_n>0 THEN RAISE_APPLICATION_ERROR(-20105,'006 ya instalada; no degrade el contexto administrativo con 005.'); END IF;
    SELECT COUNT(*) INTO v_n FROM versiones_esquema WHERE version='004';
    IF v_n<>1 OR SYS_CONTEXT('USERENV','SESSION_USER') IN ('SYS','SYSTEM') THEN
        RAISE_APPLICATION_ERROR(-20083,'Se requiere 004 y el usuario de aplicacion en el PDB.');
    END IF;
    SELECT COUNT(*) INTO v_n FROM (SELECT LOWER(TRIM(usuario)) FROM profesores GROUP BY LOWER(TRIM(usuario)) HAVING COUNT(*)>1);
    IF v_n>0 THEN RAISE_APPLICATION_ERROR(-20083,'Hay usuarios que colisionan sin distinguir mayusculas; resolver antes de migrar.'); END IF;
    SELECT COUNT(*) INTO v_n FROM (SELECT UPPER(TRIM(codigo_materia)) FROM materias GROUP BY UPPER(TRIM(codigo_materia)) HAVING COUNT(*)>1);
    IF v_n>0 THEN RAISE_APPLICATION_ERROR(-20083,'Hay codigos de materia que colisionan; resolver antes de migrar.'); END IF;
    agregar('PROFESORES','ACTIVO','activo NUMBER(1) DEFAULT 1 NOT NULL');
    agregar('ESTUDIANTES','ACTIVO','activo NUMBER(1) DEFAULT 1 NOT NULL');
    agregar('MATERIAS','ACTIVO','activo NUMBER(1) DEFAULT 1 NOT NULL');
    agregar('ESTUDIANTES','CODIGO_INSTITUCIONAL','codigo_institucional VARCHAR2(50 CHAR)');
    SELECT COUNT(*) INTO v_n FROM user_tables WHERE table_name='LIMITES_ACCESO';
    IF v_n=0 THEN EXECUTE IMMEDIATE q'~CREATE TABLE limites_acceso (
        clave VARCHAR2(64 CHAR) CONSTRAINT pk_limites_acceso PRIMARY KEY,
        intentos NUMBER DEFAULT 0 NOT NULL,
        ventana_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
        bloqueado_hasta TIMESTAMP WITH TIME ZONE,
        CONSTRAINT ck_limites_intentos CHECK(intentos>=0 AND intentos=TRUNC(intentos)))~'; END IF;
    SELECT COUNT(*) INTO v_n FROM user_tables WHERE table_name='EVENTOS_GESTION';
    IF v_n=0 THEN EXECUTE IMMEDIATE q'~CREATE TABLE eventos_gestion (
        evento_id NUMBER GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_eventos_gestion PRIMARY KEY,
        entidad VARCHAR2(20 CHAR) NOT NULL, entidad_id NUMBER NOT NULL,
        accion VARCHAR2(30 CHAR) NOT NULL, motivo VARCHAR2(500 CHAR) NOT NULL,
        actor_rol VARCHAR2(20 CHAR) NOT NULL, actor_id NUMBER,
        ocurrido_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL)~'; END IF;
END;
/
DECLARE
    v_n NUMBER;
    PROCEDURE restriccion(p_nombre VARCHAR2,p_sql VARCHAR2) IS
    BEGIN
        SELECT COUNT(*) INTO v_n FROM user_constraints WHERE constraint_name=p_nombre;
        IF v_n=0 THEN EXECUTE IMMEDIATE p_sql; END IF;
    END;
    PROCEDURE indice(p_nombre VARCHAR2,p_sql VARCHAR2) IS
    BEGIN
        SELECT COUNT(*) INTO v_n FROM user_indexes WHERE index_name=p_nombre;
        IF v_n=0 THEN EXECUTE IMMEDIATE p_sql; END IF;
    END;
BEGIN
    indice('UQ_PROFESORES_USUARIO_CI','CREATE UNIQUE INDEX uq_profesores_usuario_ci ON profesores(LOWER(TRIM(usuario)))');
    indice('UQ_MATERIAS_CODIGO_CI','CREATE UNIQUE INDEX uq_materias_codigo_ci ON materias(UPPER(TRIM(codigo_materia)))');
    indice('UQ_ESTUDIANTES_CODIGO','CREATE UNIQUE INDEX uq_estudiantes_codigo ON estudiantes(UPPER(TRIM(codigo_institucional)))');
    restriccion('CK_PROFESORES_ACTIVO','ALTER TABLE profesores ADD CONSTRAINT ck_profesores_activo CHECK(activo IN (0,1))');
    restriccion('CK_ESTUDIANTES_ACTIVO','ALTER TABLE estudiantes ADD CONSTRAINT ck_estudiantes_activo CHECK(activo IN (0,1))');
    restriccion('CK_MATERIAS_ACTIVO','ALTER TABLE materias ADD CONSTRAINT ck_materias_activo CHECK(activo IN (0,1))');
    restriccion('CK_ESTUDIANTES_CODIGO',q'~ALTER TABLE estudiantes ADD CONSTRAINT ck_estudiantes_codigo CHECK(codigo_institucional IS NULL OR REGEXP_LIKE(codigo_institucional,'^[A-Z0-9][A-Z0-9_.-]{0,49}$'))~');
END;
/
@sql/23_paquete_gestion.sql
@sql/25_paquete_clases_gestion.sql
@sql/24_politicas_gestion.sql
ALTER PACKAGE pkg_asistencia COMPILE BODY;
ALTER PACKAGE pkg_clases COMPILE BODY;
BEGIN DBMS_UTILITY.COMPILE_SCHEMA(schema=>USER,compile_all=>FALSE); END;
/
@sql/04_verificar.sql
COMMENT ON TABLE limites_acceso IS 'Ventana de intentos por SHA256 de usuario; no almacena claves ni nombres de acceso.';
COMMENT ON COLUMN estudiantes.codigo_institucional IS 'Identificador unico. NULL solo para perfiles heredados/administrativos pendientes de completar.';
INSERT INTO versiones_esquema(version,descripcion)
SELECT '005','Gestion de cuentas, codigo institucional, archivo y limites de acceso' FROM dual
WHERE NOT EXISTS(SELECT 1 FROM versiones_esquema WHERE version='005');
COMMIT;
PROMPT Migracion 005 completada; historial academico conservado.
