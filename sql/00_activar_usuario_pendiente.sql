-- Recuperacion limitada a una cuenta SIN autenticacion y SIN objetos.
-- No cambia contrasenas de cuentas activas ni reutiliza esquemas con datos.
SET ECHO OFF
SET VERIFY OFF
SET DEFINE ON
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
ACCEPT app_usuario CHAR DEFAULT 'UPC_ASISTENCIA' PROMPT 'Usuario pendiente [UPC_ASISTENCIA]: '
DECLARE
    v_usuario VARCHAR2(30) := UPPER('&&app_usuario');
    v_autenticacion VARCHAR2(30);
    v_objetos NUMBER;
BEGIN
    IF SYS_CONTEXT('USERENV', 'CON_NAME') = 'CDB$ROOT'
       OR NOT REGEXP_LIKE(v_usuario, '^[A-Z][A-Z0-9_]{0,29}$') THEN
        RAISE_APPLICATION_ERROR(-20006, 'PDB o nombre de usuario incorrecto.');
    END IF;
    SELECT authentication_type INTO v_autenticacion FROM dba_users WHERE username = v_usuario;
    SELECT COUNT(*) INTO v_objetos FROM dba_objects WHERE owner = v_usuario;
    IF v_autenticacion <> 'NONE' OR v_objetos > 0 THEN
        RAISE_APPLICATION_ERROR(-20007, 'La cuenta ya esta activa o contiene objetos. No se modifico.');
    END IF;
END;
/
PASSWORD &&app_usuario
UNDEFINE app_usuario
