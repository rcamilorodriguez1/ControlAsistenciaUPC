-- Conectar como UPC_AULA_APP. No hace DDL ni cambia filas.
DECLARE n NUMBER;
BEGIN
    IF SYS_CONTEXT('USERENV','SESSION_USER') <> 'UPC_AULA_APP'
        OR SYS_CONTEXT('USERENV','CURRENT_SCHEMA') <> 'UPC_ASISTENCIA' THEN
        RAISE_APPLICATION_ERROR(-20412,'Se requieren usuario de ejecucion y esquema propietario separados.');
    END IF;
    SELECT COUNT(*) INTO n FROM session_privs WHERE privilege <> 'CREATE SESSION';
    IF n <> 0 THEN RAISE_APPLICATION_ERROR(-20412,'Privilegios de sistema excesivos.'); END IF;
    SELECT COUNT(*) INTO n FROM session_roles;
    IF n <> 0 THEN RAISE_APPLICATION_ERROR(-20412,'La ejecucion no necesita roles.'); END IF;
    SELECT COUNT(*) INTO n FROM user_objects;
    IF n <> 0 THEN RAISE_APPLICATION_ERROR(-20412,'La cuenta de ejecucion no debe poseer objetos.'); END IF;
    SELECT COUNT(*) INTO n FROM user_ts_quotas WHERE max_bytes <> 0;
    IF n <> 0 THEN RAISE_APPLICATION_ERROR(-20412,'La ejecucion no necesita cuota de almacenamiento.'); END IF;
    SELECT COUNT(*) INTO n FROM versiones_esquema WHERE version IN ('001','002','003','004','005','006','007','008');
    IF n <> 8 THEN RAISE_APPLICATION_ERROR(-20412,'Esquema incompleto.'); END IF;
    SELECT COUNT(*) INTO n FROM all_tab_privs
        WHERE table_schema='UPC_ASISTENCIA' AND grantee=USER
        AND (grantable='YES' OR table_name IN ('PKG_ADMINISTRACION','PKG_EXCEPCIONES',
            'AUDITORIA_ASISTENCIA','HISTORIAL_MATRICULAS'));
    IF n <> 0 THEN RAISE_APPLICATION_ERROR(-20412,'Acceso reservado al propietario o administracion.'); END IF;
END;
/
