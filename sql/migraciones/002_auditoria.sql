-- Ejecutar como usuario de app en una sesion nueva, sin trabajo pendiente.
-- Reejecutable para recuperar DDL parcial; no borra tablas, historial ni versiones.
-- Iniciar SQL*Plus desde la raiz del proyecto (scripts/oracle.py lo hace).
SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
SET SERVEROUTPUT ON
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
-- No degradar un esquema posterior recompilando el disparador/vistas de 002.
DECLARE v_n NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_n FROM versiones_esquema WHERE version='003';
    IF v_n>0 THEN RAISE_APPLICATION_ERROR(-20043,'003 ya esta instalada. No reejecute 002; use scripts/oracle.py migrar.'); END IF;
END;
/
@sql/migraciones/002_estructura.sql
PROMPT Compilando contexto de auditoria...
@sql/09_paquete_auditoria.sql
PROMPT Compilando operaciones de asistencia...
@sql/11_paquete_asistencia.sql
PROMPT Creando disparadores y vistas...
@sql/10_disparadores.sql
@sql/36_recompilar_esquema.sql
@sql/04_verificar.sql
-- Registrar version solo despues de validar todos los objetos y disparadores.
INSERT INTO versiones_esquema (version, descripcion)
SELECT '002', 'Disparadores, historial, contexto por sesion y operaciones PL/SQL auditables'
FROM dual WHERE NOT EXISTS (SELECT 1 FROM versiones_esquema WHERE version = '002');
COMMIT;
PROMPT Migracion 002 completada; datos funcionales conservados.
