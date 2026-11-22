DECLARE n NUMBER; columnas NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM user_tables WHERE table_name='VERIFICACION_ESTUDIANTES';
    IF n=0 THEN RETURN; END IF;
    SELECT COUNT(*) INTO n FROM user_objects WHERE object_name='PKG_EXCEPCIONES'
        AND object_type IN ('PACKAGE','PACKAGE BODY') AND status='VALID';
    IF n<>2 THEN RAISE_APPLICATION_ERROR(-20309,'PKG_EXCEPCIONES falta o no compila.'); END IF;
    SELECT COUNT(*) INTO n FROM user_constraints WHERE table_name='VERIFICACION_ESTUDIANTES'
        AND (status<>'ENABLED' OR validated<>'VALIDATED');
    IF n<>0 THEN RAISE_APPLICATION_ERROR(-20309,'Restricciones de verificacion no habilitadas.'); END IF;
    SELECT COUNT(*) INTO columnas FROM user_tab_columns WHERE table_name='VERIFICACION_ESTUDIANTES';
    IF columnas NOT IN (16,18) THEN RAISE_APPLICATION_ERROR(-20309,'Columnas de verificacion incompletas.'); END IF;
    SELECT COUNT(*) INTO n FROM user_constraints WHERE table_name='VERIFICACION_ESTUDIANTES' AND generated='USER NAME';
    IF n<>CASE WHEN columnas=18 THEN 15 ELSE 13 END THEN
        RAISE_APPLICATION_ERROR(-20309,'Faltan restricciones de verificacion.');
    END IF;
    IF columnas=18 THEN
        EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM verificacion_estudiantes WHERE excepcion_activa=1 AND
            (documento_huella IS NULL OR clave_hash IS NULL OR
             (autorizado_por IS NULL AND autorizado_docente_por IS NULL))' INTO n;
    ELSE
        EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM verificacion_estudiantes WHERE excepcion_activa=1 AND
            (documento_huella IS NULL OR clave_hash IS NULL OR autorizado_por IS NULL)' INTO n;
    END IF;
    IF n<>0 THEN RAISE_APPLICATION_ERROR(-20309,'Hay excepciones sin respaldo administrativo.'); END IF;
    DBMS_OUTPUT.PUT_LINE('Verificacion excepcional: paquete, restricciones y autorizaciones correctos.');
END;
/
