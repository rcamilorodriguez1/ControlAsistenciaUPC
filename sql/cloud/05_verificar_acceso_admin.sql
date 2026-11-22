DECLARE n NUMBER;
BEGIN
    IF SYS_CONTEXT('USERENV','SESSION_USER') <> 'UPC_ADMIN_APP' THEN
        RAISE_APPLICATION_ERROR(-20403,'Se requiere la cuenta tecnica limitada.');
    END IF;
    SELECT COUNT(DISTINCT table_name) INTO n FROM all_tab_privs
        WHERE table_schema='UPC_ASISTENCIA' AND grantee=USER AND privilege='EXECUTE'
        AND table_name IN ('PKG_AUDITORIA','PKG_ADMINISTRACION','PKG_SESIONES','PKG_EXCEPCIONES');
    IF n <> 4 THEN RAISE_APPLICATION_ERROR(-20403,'Faltan permisos administrativos.'); END IF;
    SELECT COUNT(*) INTO n FROM UPC_ASISTENCIA.v_auditoria_asistencia WHERE 1=0;
    SELECT COUNT(*) INTO n FROM UPC_ASISTENCIA.v_historial_matriculas WHERE 1=0;
    SELECT COUNT(*) INTO n FROM UPC_ASISTENCIA.v_eventos_gestion WHERE 1=0;
END;
/
