SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
SET SERVEROUTPUT ON
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE v_n NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_n FROM versiones_esquema WHERE version='004';
    IF v_n>0 THEN RAISE_APPLICATION_ERROR(-20081,'004 ya esta instalada; no degrade las definiciones con 003. Use scripts/oracle.py migrar.'); END IF;
END;
/
@sql/migraciones/003_estructura.sql
@sql/13_paquete_clases.sql
@sql/14_integridad_clases.sql
@sql/15_vistas_clases.sql
ALTER PACKAGE pkg_asistencia COMPILE BODY;
@sql/36_recompilar_esquema.sql
@sql/04_verificar.sql
INSERT INTO versiones_esquema(version,descripcion)
SELECT '003','Clases, unicidad por estudiante, confirmacion idempotente y revision manual'
FROM dual WHERE NOT EXISTS(SELECT 1 FROM versiones_esquema WHERE version='003');
COMMIT;
PROMPT Migracion 003 completada. Registros historicos conservados.
