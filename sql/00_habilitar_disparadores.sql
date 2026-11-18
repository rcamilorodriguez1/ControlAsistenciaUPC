-- Como administrador conectado al PDB. Solo concede CREATE TRIGGER en esquema propio.
SET ECHO OFF
SET VERIFY OFF
SET DEFINE ON
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
ACCEPT app_usuario CHAR DEFAULT 'UPC_ASISTENCIA' PROMPT 'Usuario de la aplicacion [UPC_ASISTENCIA]: '
DECLARE
    v_usuario VARCHAR2(30) := UPPER('&&app_usuario');
    v_existe NUMBER;
BEGIN
    IF SYS_CONTEXT('USERENV', 'CON_NAME') = 'CDB$ROOT'
       OR NOT REGEXP_LIKE(v_usuario, '^[A-Z][A-Z0-9_]{0,29}$')
       OR v_usuario IN ('SYS', 'SYSTEM') THEN
        RAISE_APPLICATION_ERROR(-20040, 'Seleccione el PDB y un usuario de aplicacion valido.');
    END IF;
    SELECT COUNT(*) INTO v_existe FROM dba_users WHERE username = v_usuario;
    IF v_existe <> 1 THEN
        RAISE_APPLICATION_ERROR(-20041, 'El usuario de la aplicacion no existe en este PDB.');
    END IF;
    EXECUTE IMMEDIATE 'GRANT CREATE TRIGGER TO ' || DBMS_ASSERT.SIMPLE_SQL_NAME(v_usuario);
END;
/
UNDEFINE app_usuario
PROMPT Permiso CREATE TRIGGER concedido; no se cambiaron credenciales ni datos.
