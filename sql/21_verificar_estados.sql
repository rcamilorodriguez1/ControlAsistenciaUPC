DECLARE
    v_n NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='REGISTROS_ASISTENCIA' AND column_name='ESTADO_DETECCION';
    IF v_n>0 THEN
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='REGISTROS_ASISTENCIA' AND column_name='ESTADO_DETECCION' AND nullable='N';
        IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20082,'Falta el estado de deteccion obligatorio.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='REGISTROS_ASISTENCIA' AND column_name='PRESENTE_DETECTADO' AND nullable='Y';
        IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20082,'Sin muestra requiere deteccion NULL, nunca cero por defecto.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_constraints WHERE constraint_name IN ('CK_RA_ESTADO_DETECCION','CK_RA_DETECCION_COHERENTE') AND status='ENABLED' AND validated='VALIDATED';
        IF v_n<>2 THEN RAISE_APPLICATION_ERROR(-20082,'Faltan restricciones de deteccion 004.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='AUDITORIA_ASISTENCIA' AND column_name='ESTADO_ANTERIOR';
        IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20082,'Falta la instantanea del estado de deteccion.'); END IF;
        DBMS_OUTPUT.PUT_LINE('Deteccion 004: desconocido separado de ausencia; fallos no confirmables.');
    END IF;
END;
/
