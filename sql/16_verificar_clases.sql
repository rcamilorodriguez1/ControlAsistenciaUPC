DECLARE
    v_n NUMBER;
    v_clases NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_clases FROM user_tables WHERE table_name='CLASES';
    SELECT COUNT(*) INTO v_n FROM versiones_esquema WHERE version='003';
    IF v_clases>0 OR v_n>0 THEN
        IF v_clases<>1 THEN RAISE_APPLICATION_ERROR(-20080,'Falta CLASES.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_objects WHERE object_name='PKG_CLASES'
            AND object_type IN ('PACKAGE','PACKAGE BODY') AND status='VALID';
        IF v_n<>2 THEN RAISE_APPLICATION_ERROR(-20080,'PKG_CLASES incompleto.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_constraints WHERE constraint_name IN (
            'PK_CLASES','FK_CLASES_MATERIA','UQ_CLASES_INSTANTE','UQ_CLASES_MATERIA','UQ_CLASES_CONFIRMACION',
            'CK_CLASES_ESTADO','CK_CLASES_ORIGEN','CK_CLASES_LOTE','CK_CLASES_JSON','CK_CLASES_CANTIDAD','CK_CLASES_CONFIRMADA',
            'UQ_RA_CLASE_ESTUDIANTE','FK_RA_CLASE_MATERIA','CK_RA_DETECTADO','CK_RA_CORREGIDO','CK_RA_REVISION')
            AND status='ENABLED' AND validated='VALIDATED';
        IF v_n<>16 THEN RAISE_APPLICATION_ERROR(-20080,'Faltan restricciones validas de 003.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='REGISTROS_ASISTENCIA'
            AND column_name='CLASE_ID' AND nullable='N';
        IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20080,'Falta la clase obligatoria.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_triggers WHERE trigger_name IN ('TRG_ASISTENCIA_CLASE','TRG_CLASES_IDENTIDAD') AND status='ENABLED';
        IF v_n<>2 THEN RAISE_APPLICATION_ERROR(-20080,'Faltan disparadores de integridad de clases.'); END IF;
        SELECT COUNT(*) INTO v_n FROM user_views WHERE view_name='V_CLASES';
        IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20080,'Falta V_CLASES.'); END IF;
        -- SQL dinamico permite verificar tambien esquemas antiguos sin CLASES.
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='REGISTROS_ASISTENCIA' AND column_name='ESTADO_DETECCION';
        IF v_n=0 THEN
            EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM registros_asistencia WHERE clase_id IS NULL OR presente_detectado IS NULL' INTO v_n;
        ELSE
            EXECUTE IMMEDIATE q'~SELECT COUNT(*) FROM registros_asistencia WHERE clase_id IS NULL OR (presente_detectado IS NULL AND estado_deteccion<>'SIN_MUESTRA')~' INTO v_n;
        END IF;
        IF v_n<>0 THEN RAISE_APPLICATION_ERROR(-20080,'Hay asistencias sin clase/deteccion valida.'); END IF;
        DBMS_OUTPUT.PUT_LINE('Clases 003: identificacion durable, unicidad y revision inicial verificadas.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Clases 003 todavia no instaladas.');
    END IF;
END;
/
