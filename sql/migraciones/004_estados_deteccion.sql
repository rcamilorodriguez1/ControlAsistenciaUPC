-- Aplicacion detenida, sesion nueva y respaldo previo (scripts/oracle.py migrar lo crea).
SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
SET SERVEROUTPUT ON
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE v_n NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_n FROM versiones_esquema WHERE version='005';
    IF v_n>0 THEN RAISE_APPLICATION_ERROR(-20083,'005 ya esta instalada; use scripts/oracle.py migrar.'); END IF;
END;
/
DECLARE
    v_n NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_n FROM versiones_esquema WHERE version='003';
    IF v_n<>1 OR SYS_CONTEXT('USERENV','SESSION_USER') IN ('SYS','SYSTEM') THEN
        RAISE_APPLICATION_ERROR(-20081,'Se requiere 003 y el usuario de aplicacion en el PDB.');
    END IF;
    SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='REGISTROS_ASISTENCIA' AND column_name='ESTADO_DETECCION';
    IF v_n=0 THEN EXECUTE IMMEDIATE 'ALTER TABLE registros_asistencia ADD estado_deteccion VARCHAR2(20 CHAR)'; END IF;
    EXECUTE IMMEDIATE q'~UPDATE registros_asistencia SET estado_deteccion=CASE presente_detectado WHEN 1 THEN 'PRESENTE' ELSE 'AUSENTE' END WHERE estado_deteccion IS NULL~';
    COMMIT;
    SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='REGISTROS_ASISTENCIA' AND column_name='ESTADO_DETECCION' AND nullable='Y';
    IF v_n>0 THEN EXECUTE IMMEDIATE 'ALTER TABLE registros_asistencia MODIFY estado_deteccion NOT NULL'; END IF;
    SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='REGISTROS_ASISTENCIA' AND column_name='PRESENTE_DETECTADO' AND nullable='N';
    IF v_n>0 THEN EXECUTE IMMEDIATE 'ALTER TABLE registros_asistencia MODIFY presente_detectado NULL'; END IF;
    SELECT COUNT(*) INTO v_n FROM user_constraints WHERE constraint_name='CK_RA_ESTADO_DETECCION';
    IF v_n=0 THEN EXECUTE IMMEDIATE q'~ALTER TABLE registros_asistencia ADD CONSTRAINT ck_ra_estado_deteccion CHECK (estado_deteccion IN ('PRESENTE','AUSENTE','SIN_MUESTRA'))~'; END IF;
    SELECT COUNT(*) INTO v_n FROM user_constraints WHERE constraint_name='CK_RA_DETECCION_COHERENTE';
    IF v_n=0 THEN EXECUTE IMMEDIATE q'~ALTER TABLE registros_asistencia ADD CONSTRAINT ck_ra_deteccion_coherente CHECK (
        (estado_deteccion='SIN_MUESTRA' AND presente_detectado IS NULL AND corregido_manual=1)
        OR (estado_deteccion='PRESENTE' AND presente_detectado IS NOT NULL AND presente_detectado=1)
        OR (estado_deteccion='AUSENTE' AND presente_detectado IS NOT NULL AND presente_detectado=0))~'; END IF;
    SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='AUDITORIA_ASISTENCIA' AND column_name='ESTADO_ANTERIOR';
    IF v_n=0 THEN EXECUTE IMMEDIATE 'ALTER TABLE auditoria_asistencia ADD estado_anterior VARCHAR2(20 CHAR)'; END IF;
    EXECUTE IMMEDIATE q'~UPDATE auditoria_asistencia SET estado_anterior=CASE detectado_anterior WHEN 1 THEN 'PRESENTE' WHEN 0 THEN 'AUSENTE' END WHERE estado_anterior IS NULL~';
    COMMIT;
END;
/
@sql/18_paquete_clases_estados.sql
@sql/19_integridad_estados.sql
@sql/20_vistas_estados.sql
ALTER PACKAGE pkg_asistencia COMPILE BODY;
@sql/36_recompilar_esquema.sql
@sql/04_verificar.sql
COMMENT ON COLUMN registros_asistencia.estado_deteccion IS 'Resultado original: PRESENTE/AUSENTE o SIN_MUESTRA. Un fallo global no se confirma.';
COMMENT ON COLUMN registros_asistencia.presente_detectado IS 'NULL cuando no hay muestra; nunca usar NVL para convertirlo en ausencia.';
INSERT INTO versiones_esquema(version,descripcion)
SELECT '004','Deteccion desconocida separada de ausencia y resolucion manual obligatoria'
FROM dual WHERE NOT EXISTS(SELECT 1 FROM versiones_esquema WHERE version='004');
COMMIT;
PROMPT Migracion 004 completada sin convertir detecciones desconocidas en ausencias.
