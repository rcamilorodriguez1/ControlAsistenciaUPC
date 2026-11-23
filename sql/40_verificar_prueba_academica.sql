DECLARE n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM user_constraints
    WHERE table_name='VERIFICACION_ESTUDIANTES'
      AND constraint_name IN ('CK_VERIFICACION_ESTADO','CK_VERIFICACION_RESULTADO')
      AND status='ENABLED' AND validated='VALIDATED'
      AND search_condition_vc LIKE '%PRUEBA_ACADEMICA%';
    IF n<>2 THEN RAISE_APPLICATION_ERROR(-20312,'Faltan las reglas del estado academico de prueba.'); END IF;
END;
/
