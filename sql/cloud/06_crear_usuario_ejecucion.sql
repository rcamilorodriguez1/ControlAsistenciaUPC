-- Solo preparar_ejecucion_cloud.py; clave enlazada, nunca sustituida en un SQL publico.
DECLARE
    n NUMBER;
    clave VARCHAR2(30) := :clave_ejecucion;
BEGIN
    IF SYS_CONTEXT('USERENV','SESSION_USER') <> 'ADMIN' THEN
        RAISE_APPLICATION_ERROR(-20410,'Se requiere ADMIN de Autonomous.');
    END IF;
    SELECT COUNT(*) INTO n FROM all_users WHERE username='UPC_AULA_APP';
    IF n <> 0 THEN
        RAISE_APPLICATION_ERROR(-20410,'UPC_AULA_APP ya existe; no se reemplaza ni cambia su clave.');
    END IF;
    IF NOT REGEXP_LIKE(clave,'^[A-Za-z][A-Za-z0-9_]{11,29}$','c') THEN
        RAISE_APPLICATION_ERROR(-20410,'Formato de clave tecnica no admitido.');
    END IF;
    EXECUTE IMMEDIATE 'CREATE USER UPC_AULA_APP IDENTIFIED BY "' || clave || '"';
    EXECUTE IMMEDIATE 'GRANT CREATE SESSION TO UPC_AULA_APP';
END;
/
