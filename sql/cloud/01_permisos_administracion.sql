-- Ejecutar como UPC_ASISTENCIA DESPUES de instalar 001-008 en Autonomous.
-- Permisos directos al usuario tecnico, equivalentes al rol local limitado.
SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE n NUMBER;
BEGIN
    IF SYS_CONTEXT('USERENV','SESSION_USER') <> 'UPC_ASISTENCIA' THEN
        RAISE_APPLICATION_ERROR(-20401,'Conectar como UPC_ASISTENCIA.');
    END IF;
    SELECT COUNT(*) INTO n FROM versiones_esquema WHERE version='008';
    IF n <> 1 THEN RAISE_APPLICATION_ERROR(-20401,'Instalar y verificar 008 primero.'); END IF;
    SELECT COUNT(*) INTO n FROM user_objects
        WHERE object_name IN ('PKG_AUDITORIA','PKG_ADMINISTRACION','PKG_SESIONES','PKG_EXCEPCIONES')
        AND object_type='PACKAGE BODY' AND status='VALID';
    IF n <> 4 THEN RAISE_APPLICATION_ERROR(-20401,'Hay paquetes administrativos ausentes o invalidos.'); END IF;
END;
/
GRANT EXECUTE ON pkg_auditoria TO UPC_ADMIN_APP;
GRANT EXECUTE ON pkg_administracion TO UPC_ADMIN_APP;
GRANT EXECUTE ON pkg_sesiones TO UPC_ADMIN_APP;
GRANT EXECUTE ON pkg_excepciones TO UPC_ADMIN_APP;
GRANT SELECT ON v_auditoria_asistencia TO UPC_ADMIN_APP;
GRANT SELECT ON v_historial_matriculas TO UPC_ADMIN_APP;
GRANT SELECT ON v_eventos_gestion TO UPC_ADMIN_APP;
PROMPT Cuenta administrativa limitada preparada. No se concedio DML directo sobre tablas.
