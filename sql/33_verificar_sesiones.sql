DECLARE n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM user_tables WHERE table_name='SESIONES_USUARIO';
    IF n>0 THEN
        SELECT COUNT(*) INTO n FROM user_objects WHERE object_name='PKG_SESIONES' AND object_type IN ('PACKAGE','PACKAGE BODY') AND status='VALID';
        IF n<>2 THEN RAISE_APPLICATION_ERROR(-20211,'El paquete de sesiones no esta valido.'); END IF;
        SELECT COUNT(*) INTO n FROM user_constraints WHERE constraint_name IN ('PK_SESIONES_USUARIO','CK_SESIONES_ROL','CK_SESIONES_ACTOR','CK_SESIONES_HASH','CK_SESIONES_FECHAS') AND status='ENABLED' AND validated='VALIDATED';
        IF n<>5 THEN RAISE_APPLICATION_ERROR(-20211,'Restricciones de sesiones invalidas.'); END IF;
        DBMS_OUTPUT.PUT_LINE('Sesiones 007 verificadas.');
    END IF;
END;
/
