-- Ejecutar como SYS en el PDB; preparar_administracion.py aporta entradas por stdin.
SET ECHO OFF
SET VERIFY OFF
SET DEFINE ON
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
ACCEPT propietario CHAR PROMPT 'Esquema del proyecto: '
ACCEPT usuario_admin CHAR PROMPT 'Usuario tecnico administrativo: '
ACCEPT rol_admin CHAR PROMPT 'Rol administrativo: '
ACCEPT clave_admin CHAR PROMPT 'Clave tecnica: ' HIDE
DECLARE v_n NUMBER;
BEGIN
    IF SYS_CONTEXT('USERENV','CON_NAME')='CDB$ROOT' OR SYS_CONTEXT('USERENV','SESSION_USER')<>'SYS' THEN
        RAISE_APPLICATION_ERROR(-20110,'Ejecutar como SYS en el PDB del proyecto.'); END IF;
    SELECT COUNT(*) INTO v_n FROM dba_users WHERE username=UPPER('&usuario_admin');
    IF v_n<>0 THEN RAISE_APPLICATION_ERROR(-20110,'El usuario tecnico ya existe; no se reemplazo.'); END IF;
    SELECT COUNT(*) INTO v_n FROM dba_roles WHERE role=UPPER('&rol_admin');
    IF v_n<>0 THEN RAISE_APPLICATION_ERROR(-20110,'El rol ya existe; no se reemplazo.'); END IF;
    SELECT COUNT(*) INTO v_n FROM dba_objects WHERE owner=UPPER('&propietario') AND object_name IN ('PKG_ADMINISTRACION','PKG_SESIONES','PKG_EXCEPCIONES','PKG_EXCEPCIONES_DOCENTES') AND object_type='PACKAGE BODY' AND status='VALID';
    IF v_n<>4 THEN RAISE_APPLICATION_ERROR(-20110,'Instalar y verificar 009 antes de los permisos.'); END IF;
END;
/
CREATE ROLE &rol_admin;
CREATE USER &usuario_admin IDENTIFIED BY "&clave_admin";
GRANT CREATE SESSION TO &usuario_admin;
GRANT EXECUTE ON &propietario..pkg_auditoria TO &rol_admin;
GRANT EXECUTE ON &propietario..pkg_administracion TO &rol_admin;
GRANT EXECUTE ON &propietario..pkg_sesiones TO &rol_admin;
GRANT EXECUTE ON &propietario..pkg_excepciones TO &rol_admin;
GRANT EXECUTE ON &propietario..pkg_excepciones_docentes TO &rol_admin;
GRANT SELECT ON &propietario..v_auditoria_asistencia TO &rol_admin;
GRANT SELECT ON &propietario..v_historial_matriculas TO &rol_admin;
GRANT SELECT ON &propietario..v_eventos_gestion TO &rol_admin;
GRANT &rol_admin TO &usuario_admin;
UNDEFINE propietario usuario_admin rol_admin clave_admin
SET DEFINE OFF
PROMPT Permisos administrativos limitados asignados; sin DBA ni DML directo sobre tablas.
