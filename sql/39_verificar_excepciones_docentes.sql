DECLARE n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM user_tab_columns WHERE table_name='VERIFICACION_ESTUDIANTES'
        AND column_name='AUTORIZADO_DOCENTE_POR';
    IF n=0 THEN RETURN; END IF;
    SELECT COUNT(*) INTO n FROM user_objects WHERE object_name='PKG_EXCEPCIONES_DOCENTES'
        AND object_type IN ('PACKAGE','PACKAGE BODY') AND status='VALID';
    IF n<>2 THEN RAISE_APPLICATION_ERROR(-20319,'Falta el paquete docente compilado.'); END IF;
    SELECT COUNT(*) INTO n FROM user_constraints WHERE table_name='VERIFICACION_ESTUDIANTES'
        AND constraint_name IN ('FK_VERIFICACION_DOCENTE','FK_VERIFICACION_MATERIA')
        AND status='ENABLED' AND validated='VALIDATED';
    IF n<>2 THEN RAISE_APPLICATION_ERROR(-20319,'Faltan las relaciones de autorizacion docente.'); END IF;
    SELECT COUNT(*) INTO n FROM user_tab_privs WHERE table_name='PKG_EXCEPCIONES_DOCENTES'
        AND privilege='EXECUTE' AND grantee IN ('PUBLIC','UPC_AULA_APP','UPC_ROL_APP');
    IF n<>0 THEN RAISE_APPLICATION_ERROR(-20319,'El paquete docente no se concede al runtime general.'); END IF;
END;
/
