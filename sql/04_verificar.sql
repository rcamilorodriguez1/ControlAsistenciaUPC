SET LINESIZE 180
SET PAGESIZE 100
SET SERVEROUTPUT ON
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
SELECT USER AS usuario, SYS_CONTEXT('USERENV', 'CON_NAME') AS pdb FROM dual;
SELECT table_name FROM user_tables ORDER BY table_name;
SELECT view_name FROM user_views ORDER BY view_name;
SELECT object_name, object_type, status FROM user_objects
WHERE object_type IN ('PACKAGE', 'PACKAGE BODY') ORDER BY object_type;
SELECT name, type, line, text FROM user_errors ORDER BY name, sequence;
SELECT * FROM versiones_esquema;
DECLARE
    v_cantidad NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_cantidad FROM user_tables
    WHERE table_name IN ('PROFESORES', 'ESTUDIANTES', 'MATERIAS',
                         'MATERIA_ESTUDIANTES', 'REGISTROS_ASISTENCIA', 'VERSIONES_ESQUEMA');
    IF v_cantidad <> 6 THEN
        RAISE_APPLICATION_ERROR(-20022, 'Faltan tablas de la instalacion inicial.');
    END IF;
    SELECT COUNT(*) INTO v_cantidad FROM user_views
    WHERE view_name IN ('V_PROFESORES', 'V_ESTUDIANTES', 'V_MATERIAS', 'V_MATERIA_ESTUDIANTES',
                        'V_REGISTROS_ASISTENCIA', 'V_RESUMEN_MATERIAS', 'V_VERSIONES_ESQUEMA');
    IF v_cantidad <> 7 THEN
        RAISE_APPLICATION_ERROR(-20023, 'Faltan vistas de la instalacion inicial.');
    END IF;
    SELECT COUNT(*) INTO v_cantidad FROM user_objects
    WHERE object_name = 'PKG_ASISTENCIA' AND object_type IN ('PACKAGE', 'PACKAGE BODY');
    IF v_cantidad <> 2 THEN
        RAISE_APPLICATION_ERROR(-20024, 'Falta la especificacion o cuerpo del paquete.');
    END IF;
    SELECT COUNT(*) INTO v_cantidad FROM user_constraints
    WHERE constraint_name IN (
        'PK_VERSIONES_ESQUEMA', 'PK_PROFESORES', 'PK_ESTUDIANTES', 'PK_MATERIAS',
        'PK_MATERIA_ESTUDIANTES', 'PK_REGISTROS_ASISTENCIA',
        'UQ_PROFESORES_USUARIO', 'UQ_MATERIAS_CODIGO',
        'FK_MATERIAS_PROFESOR', 'FK_ME_MATERIA', 'FK_ME_ESTUDIANTE',
        'FK_RA_MATERIA', 'FK_RA_ESTUDIANTE',
        'CK_ESTUDIANTES_FACIAL_JSON', 'CK_ESTUDIANTES_VOZ_JSON', 'CK_ASISTENCIA_PRESENTE'
    ) AND status = 'ENABLED' AND validated = 'VALIDATED';
    IF v_cantidad <> 16 THEN
        RAISE_APPLICATION_ERROR(-20025, 'Faltan restricciones esperadas o estan deshabilitadas/sin validar.');
    END IF;
    SELECT COUNT(*) INTO v_cantidad FROM user_errors;
    IF v_cantidad > 0 THEN
        RAISE_APPLICATION_ERROR(-20020, 'Hay errores de compilacion. Revise USER_ERRORS.');
    END IF;
    SELECT COUNT(*) INTO v_cantidad FROM user_objects WHERE status <> 'VALID';
    IF v_cantidad > 0 THEN
        RAISE_APPLICATION_ERROR(-20021, 'Hay objetos invalidos. Revise USER_OBJECTS.');
    END IF;
    DBMS_OUTPUT.PUT_LINE('Verificacion correcta: sin errores ni objetos invalidos.');
END;
/
@@08_verificar_auditoria.sql
@@16_verificar_clases.sql
@@21_verificar_estados.sql
@@26_verificar_gestion.sql
@@29_verificar_administracion.sql
@@33_verificar_sesiones.sql
@@35_verificar_excepciones.sql
@@39_verificar_excepciones_docentes.sql
