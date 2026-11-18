-- Ejecutar como administrador, conectado al PDB de la aplicacion.
-- En Oracle XE local: sqlplus / as sysdba
-- SQL> ALTER SESSION SET CONTAINER = XEPDB1;
-- SQL> @sql/00_crear_usuario.sql
SET ECHO OFF
SET VERIFY OFF
SET SERVEROUTPUT ON
SET DEFINE ON
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
ACCEPT app_usuario CHAR DEFAULT 'UPC_ASISTENCIA' PROMPT 'Nuevo usuario [UPC_ASISTENCIA]: '

DECLARE
    v_usuario VARCHAR2(30) := UPPER('&&app_usuario');
    v_existe NUMBER;
BEGIN
    IF SYS_CONTEXT('USERENV', 'CON_NAME') = 'CDB$ROOT' THEN
        RAISE_APPLICATION_ERROR(-20001, 'Conectese al PDB antes de crear el usuario.');
    END IF;
    IF NOT REGEXP_LIKE(v_usuario, '^[A-Z][A-Z0-9_]{0,29}$') THEN
        RAISE_APPLICATION_ERROR(-20002, 'Nombre no valido. Use letras, numeros y guion bajo.');
    END IF;
    SELECT COUNT(*) INTO v_existe FROM dba_users WHERE username = v_usuario;
    IF v_existe > 0 THEN
        RAISE_APPLICATION_ERROR(-20003, 'El usuario ya existe. No se modifico su cuenta ni sus datos.');
    END IF;
    EXECUTE IMMEDIATE 'CREATE USER ' || DBMS_ASSERT.SIMPLE_SQL_NAME(v_usuario)
        || ' NO AUTHENTICATION DEFAULT TABLESPACE USERS QUOTA 100M ON USERS';
    EXECUTE IMMEDIATE 'GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, '
        || 'CREATE PROCEDURE, CREATE SEQUENCE, CREATE TRIGGER TO ' || DBMS_ASSERT.SIMPLE_SQL_NAME(v_usuario);
END;
/
-- PASSWORD pide la clave dos veces sin incorporarla a un fichero SQL.
PASSWORD &&app_usuario
UNDEFINE app_usuario
PROMPT Usuario preparado. Instale las tablas conectado como ese usuario.
