-- Compatible con 001: comprueba 002 si hay version registrada o estructura parcial.
DECLARE
    v_version NUMBER;
    v_tablas NUMBER;
    v_cantidad NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_version FROM versiones_esquema WHERE version = '002';
    SELECT COUNT(*) INTO v_tablas FROM user_tables
    WHERE table_name IN ('AUDITORIA_ASISTENCIA', 'HISTORIAL_MATRICULAS');
    IF v_version > 0 OR v_tablas > 0 THEN
        IF v_tablas <> 2 THEN RAISE_APPLICATION_ERROR(-20045, 'Faltan tablas de auditoria de 002.'); END IF;
        SELECT COUNT(*) INTO v_cantidad FROM user_tab_columns
        WHERE table_name IN ('PROFESORES', 'ESTUDIANTES', 'MATERIAS') AND column_name = 'ACTUALIZADO_EN'
          AND data_type LIKE 'TIMESTAMP%WITH TIME ZONE' AND nullable = 'N';
        IF v_cantidad <> 3 THEN RAISE_APPLICATION_ERROR(-20046, 'Faltan columnas ACTUALIZADO_EN con zona horaria y NOT NULL.'); END IF;
        SELECT COUNT(*) INTO v_cantidad FROM user_objects
        WHERE object_name IN ('PKG_AUDITORIA', 'PKG_ASISTENCIA')
          AND object_type IN ('PACKAGE', 'PACKAGE BODY') AND status = 'VALID';
        IF v_cantidad <> 4 THEN RAISE_APPLICATION_ERROR(-20047, 'Hay paquetes de auditoria/asistencia incompletos.'); END IF;
        SELECT COUNT(*) INTO v_cantidad FROM user_triggers
        WHERE trigger_name IN ('TRG_ASISTENCIA_AUD', 'TRG_MATRICULAS_HIST',
            'TRG_PROFESORES_ACTUALIZADO', 'TRG_ESTUDIANTES_ACTUALIZADO', 'TRG_MATERIAS_ACTUALIZADO')
          AND status = 'ENABLED';
        IF v_cantidad <> 5 THEN RAISE_APPLICATION_ERROR(-20048, 'Faltan disparadores activos de la version 002.'); END IF;
        SELECT COUNT(*) INTO v_cantidad FROM user_views
        WHERE view_name IN ('V_AUDITORIA_ASISTENCIA', 'V_HISTORIAL_MATRICULAS');
        IF v_cantidad <> 2 THEN RAISE_APPLICATION_ERROR(-20049, 'Faltan vistas de auditoria.'); END IF;
        SELECT COUNT(*) INTO v_cantidad FROM user_constraints
        WHERE constraint_name IN ('PK_AUDITORIA_ASISTENCIA', 'PK_HISTORIAL_MATRICULAS',
            'CK_AUDASIST_OPERACION', 'CK_AUDASIST_ANT', 'CK_AUDASIST_NUEVO', 'CK_AUDASIST_ROL',
            'CK_HISTMAT_ACCION', 'CK_HISTMAT_ROL') AND status = 'ENABLED' AND validated = 'VALIDATED';
        IF v_cantidad <> 8 THEN RAISE_APPLICATION_ERROR(-20050, 'Faltan restricciones validas de auditoria.'); END IF;
        DBMS_OUTPUT.PUT_LINE('Auditoria 002: dos tablas, cinco disparadores y dos paquetes completos.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Esquema 001: auditoria 002 todavia no instalada.');
    END IF;
END;
/
