DECLARE n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM user_procedures WHERE
        (object_name='PKG_GESTION' AND procedure_name IN ('REGISTRAR_ESTUDIANTE','ACTUALIZAR_DOCUMENTO')) OR
        (object_name='PKG_ADMINISTRACION' AND procedure_name='ACTUALIZAR_DOCUMENTO');
    IF n<>3 THEN RAISE_APPLICATION_ERROR(-20314,'Faltan operaciones de documento estudiantil.'); END IF;
    SELECT COUNT(*) INTO n FROM user_errors WHERE attribute='ERROR';
    IF n<>0 THEN RAISE_APPLICATION_ERROR(-20314,'Existen errores de compilacion.'); END IF;
END;
/
