-- SOLO una base Autonomous nueva, conectado como ADMIN mediante SQLcl o SQL*Plus.
-- No usar en Oracle XE ni en un esquema que ya contenga el proyecto.
SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE n NUMBER;
BEGIN
    IF SYS_CONTEXT('USERENV','SESSION_USER') <> 'ADMIN' THEN
        RAISE_APPLICATION_ERROR(-20400,'Conectar como ADMIN de Autonomous Database.');
    END IF;
    SELECT COUNT(*) INTO n FROM all_users WHERE username IN ('UPC_ASISTENCIA','UPC_ADMIN_APP');
    IF n <> 0 THEN
        RAISE_APPLICATION_ERROR(-20400,'Ya existe una cuenta del proyecto. No se reemplazo ninguna.');
    END IF;
END;
/
-- Sin autenticación hasta establecer las contraseñas con el comando PASSWORD.
-- DATA es el tablespace de Autonomous; no se concede DWROLE, DBA ni cuotas ilimitadas.
CREATE USER UPC_ASISTENCIA NO AUTHENTICATION DEFAULT TABLESPACE DATA QUOTA 100M ON DATA;
GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE PROCEDURE,
    CREATE SEQUENCE, CREATE TRIGGER TO UPC_ASISTENCIA;
CREATE USER UPC_ADMIN_APP NO AUTHENTICATION;
GRANT CREATE SESSION TO UPC_ADMIN_APP;
PROMPT Establece las dos claves Oracle. Guardarlas en el gestor privado, no en este archivo.
PASSWORD UPC_ASISTENCIA
PASSWORD UPC_ADMIN_APP
PROMPT Reconectar como UPC_ASISTENCIA y ejecutar @oracle_scripts.sql desde la raiz del repositorio.
