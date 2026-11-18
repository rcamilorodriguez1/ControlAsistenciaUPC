DECLARE v_n NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_n FROM user_tables WHERE table_name='ADMINISTRADORES';
    IF v_n>0 THEN
        SELECT COUNT(*) INTO v_n FROM user_objects WHERE object_name='PKG_ADMINISTRACION' AND object_type IN ('PACKAGE','PACKAGE BODY') AND status='VALID';
        IF v_n<>2 THEN RAISE_APPLICATION_ERROR(-20104,'El paquete administrativo no esta valido.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='EVENTOS_GESTION' AND column_name IN ('VALORES_ANTERIORES','VALORES_NUEVOS');
        IF v_n<>2 THEN RAISE_APPLICATION_ERROR(-20104,'Faltan instantaneas administrativas.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_constraints WHERE constraint_name IN ('CK_AUDASIST_ROL','CK_HISTMAT_ROL') AND status='ENABLED' AND validated='VALIDATED';
        IF v_n<>2 THEN RAISE_APPLICATION_ERROR(-20104,'Restricciones de actores invalidas.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name IN ('PROFESORES','ESTUDIANTES','MATERIAS') AND column_name='VERSION_EDICION' AND nullable='N' AND data_type='NUMBER';
        IF v_n<>3 THEN RAISE_APPLICATION_ERROR(-20104,'Faltan versiones de edicion obligatorias.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_triggers WHERE trigger_name='TRG_ADMINISTRADORES_ACTUALIZADO' AND status='ENABLED';
        IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20104,'Falta el disparador administrativo activo.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_constraints WHERE constraint_name IN ('PK_ADMINISTRADORES','CK_ADMINISTRADORES_ACTIVO','CK_EVENTOS_ANTES_JSON','CK_EVENTOS_DESPUES_JSON') AND status='ENABLED' AND validated='VALIDATED';
        IF v_n<>4 THEN RAISE_APPLICATION_ERROR(-20104,'Restricciones administrativas invalidas.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_indexes WHERE index_name='UQ_ADMINISTRADORES_USUARIO' AND uniqueness='UNIQUE' AND status='VALID';
        IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20104,'Falta el indice unico de administradores.'); END IF;
        DBMS_OUTPUT.PUT_LINE('Administracion 006 verificada.');
    END IF;
END;
/
