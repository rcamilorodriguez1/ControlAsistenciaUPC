DECLARE v_n NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_n FROM user_tables WHERE table_name='LIMITES_ACCESO';
    IF v_n>0 THEN
        SELECT COUNT(*) INTO v_n FROM user_objects WHERE object_name='PKG_GESTION' AND object_type IN ('PACKAGE','PACKAGE BODY') AND status='VALID';
        IF v_n<>2 THEN RAISE_APPLICATION_ERROR(-20089,'PKG_GESTION no esta completo.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE column_name='ACTIVO' AND table_name IN ('PROFESORES','ESTUDIANTES','MATERIAS') AND nullable='N';
        IF v_n<>3 THEN RAISE_APPLICATION_ERROR(-20089,'Faltan estados de cuenta/materia.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_tables WHERE table_name IN ('LIMITES_ACCESO','EVENTOS_GESTION');
        IF v_n<>2 THEN RAISE_APPLICATION_ERROR(-20089,'Falta gestion de acceso/eventos.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_indexes WHERE index_name IN ('UQ_PROFESORES_USUARIO_CI','UQ_MATERIAS_CODIGO_CI','UQ_ESTUDIANTES_CODIGO') AND status='VALID';
        IF v_n<>3 THEN RAISE_APPLICATION_ERROR(-20089,'Faltan indices de unicidad normalizada.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_triggers WHERE trigger_name IN ('TRG_MATRICULA_ACTIVA','TRG_ASISTENCIA_ACTIVA') AND status='ENABLED';
        IF v_n<>2 THEN RAISE_APPLICATION_ERROR(-20089,'Faltan reglas de actividad.'); END IF;
        DBMS_OUTPUT.PUT_LINE('Gestion 005 verificada: cuentas, codigo institucional, actividad y eventos.');
    END IF;
END;
/
