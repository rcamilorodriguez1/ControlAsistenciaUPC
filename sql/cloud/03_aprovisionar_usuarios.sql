-- Bloque parametrizado para preparar_oracle_cloud.py. Las claves no se almacenan en SQL.
DECLARE
    n NUMBER;
    clave_propietario VARCHAR2(30) := :clave_propietario;
    clave_administracion VARCHAR2(30) := :clave_administracion;
BEGIN
    IF SYS_CONTEXT('USERENV','SESSION_USER') <> 'ADMIN' THEN
        RAISE_APPLICATION_ERROR(-20400,'Se requiere ADMIN de Autonomous.');
    END IF;
    SELECT COUNT(*) INTO n FROM all_users
        WHERE username IN ('UPC_ASISTENCIA','UPC_ADMIN_APP');
    IF n <> 0 THEN RAISE_APPLICATION_ERROR(-20400,'Ya existe una cuenta; no se reemplazo.'); END IF;
    IF NOT REGEXP_LIKE(clave_propietario,'^[A-Za-z][A-Za-z0-9_]{11,29}$','c')
        OR NOT REGEXP_LIKE(clave_administracion,'^[A-Za-z][A-Za-z0-9_]{11,29}$','c') THEN
        RAISE_APPLICATION_ERROR(-20400,'Formato de claves tecnicas no admitido.');
    END IF;
    EXECUTE IMMEDIATE 'CREATE USER UPC_ASISTENCIA IDENTIFIED BY "' || clave_propietario ||
        '" DEFAULT TABLESPACE DATA QUOTA 100M ON DATA';
    EXECUTE IMMEDIATE 'GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE PROCEDURE, '
        || 'CREATE SEQUENCE, CREATE TRIGGER TO UPC_ASISTENCIA';
    EXECUTE IMMEDIATE 'CREATE USER UPC_ADMIN_APP IDENTIFIED BY "' || clave_administracion || '"';
    EXECUTE IMMEDIATE 'GRANT CREATE SESSION TO UPC_ADMIN_APP';
END;
/
