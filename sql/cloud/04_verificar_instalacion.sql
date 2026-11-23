DECLARE n NUMBER;
BEGIN
    IF SYS_CONTEXT('USERENV','SESSION_USER') <> 'UPC_ASISTENCIA' THEN
        RAISE_APPLICATION_ERROR(-20402,'Se requiere el propietario UPC_ASISTENCIA.');
    END IF;
    SELECT COUNT(*) INTO n FROM versiones_esquema
        WHERE version IN ('001','002','003','004','005','006','007','008','009','010','011');
    IF n <> 11 THEN RAISE_APPLICATION_ERROR(-20402,'Faltan versiones del esquema.'); END IF;
    SELECT COUNT(*) INTO n FROM user_objects WHERE status <> 'VALID';
    IF n <> 0 THEN RAISE_APPLICATION_ERROR(-20402,'Existen objetos invalidos.'); END IF;
    SELECT COUNT(*) INTO n FROM user_errors WHERE attribute='ERROR';
    IF n <> 0 THEN RAISE_APPLICATION_ERROR(-20402,'Existen errores de compilacion.'); END IF;
    SELECT COUNT(*) INTO n FROM user_triggers WHERE status <> 'ENABLED';
    IF n <> 0 THEN RAISE_APPLICATION_ERROR(-20402,'Existen disparadores deshabilitados.'); END IF;
    SELECT COUNT(*) INTO n FROM user_tables;
    IF n <> 14 THEN RAISE_APPLICATION_ERROR(-20402,'Se esperaban 14 tablas.'); END IF;
    SELECT COUNT(*) INTO n FROM user_views;
    IF n <> 11 THEN RAISE_APPLICATION_ERROR(-20402,'Se esperaban 11 vistas.'); END IF;
    SELECT COUNT(*) INTO n FROM user_triggers;
    IF n <> 10 THEN RAISE_APPLICATION_ERROR(-20402,'Se esperaban 10 disparadores.'); END IF;
    SELECT COUNT(*) INTO n FROM user_objects WHERE object_type='PACKAGE BODY' AND status='VALID';
    IF n <> 8 THEN RAISE_APPLICATION_ERROR(-20402,'Se esperaban 8 paquetes compilados.'); END IF;
END;
/
