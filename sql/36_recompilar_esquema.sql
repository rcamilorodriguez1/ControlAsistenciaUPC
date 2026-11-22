-- Las modificaciones de tablas pueden invalidar vistas y paquetes dependientes.
-- Recompilar el propio esquema antes de verificar; los errores reales siguen fallando.
BEGIN
    IF SYS_CONTEXT('USERENV','SESSION_USER') IN ('SYS','SYSTEM','ADMIN')
       OR SYS_CONTEXT('USERENV','CON_NAME')='CDB$ROOT' THEN
        RAISE_APPLICATION_ERROR(-20404,'Recompilar conectado como propietario del proyecto.');
    END IF;
    DBMS_UTILITY.COMPILE_SCHEMA(schema=>USER, compile_all=>FALSE);
END;
/
