-- Amplia el ultimo metodo de acceso; no concede excepciones ni modifica credenciales.
SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM versiones_esquema WHERE version='009';
    IF n<>1 OR USER IN ('SYS','SYSTEM') THEN
        RAISE_APPLICATION_ERROR(-20312,'Se requiere 009 y el propietario del proyecto.');
    END IF;
    SELECT COUNT(*) INTO n FROM user_constraints WHERE constraint_name='CK_VERIFICACION_ESTADO';
    IF n=1 THEN EXECUTE IMMEDIATE 'ALTER TABLE verificacion_estudiantes DROP CONSTRAINT ck_verificacion_estado'; END IF;
    EXECUTE IMMEDIATE 'ALTER TABLE verificacion_estudiantes ADD CONSTRAINT ck_verificacion_estado CHECK
        (estado_verificacion IN (''PENDIENTE'',''BIOMETRICA_COMPLETA'',''EXCEPCIONAL'',''PRUEBA_ACADEMICA''))';
    SELECT COUNT(*) INTO n FROM user_constraints WHERE constraint_name='CK_VERIFICACION_RESULTADO';
    IF n=1 THEN EXECUTE IMMEDIATE 'ALTER TABLE verificacion_estudiantes DROP CONSTRAINT ck_verificacion_resultado'; END IF;
    EXECUTE IMMEDIATE 'ALTER TABLE verificacion_estudiantes ADD CONSTRAINT ck_verificacion_resultado CHECK
        ((estado_verificacion=''PENDIENTE'' AND verificado_en IS NULL AND factores_verificados=0) OR
         (estado_verificacion IN (''EXCEPCIONAL'',''PRUEBA_ACADEMICA'') AND verificado_en IS NOT NULL AND factores_verificados=0) OR
         (estado_verificacion=''BIOMETRICA_COMPLETA'' AND verificado_en IS NOT NULL AND factores_verificados>=factores_requeridos))';
END;
/
@sql/36_recompilar_esquema.sql
@sql/40_verificar_prueba_academica.sql
INSERT INTO versiones_esquema(version,descripcion)
SELECT '010','Metodo de acceso temporal para demostracion academica, sin autorizacion excepcional individual' FROM dual
WHERE NOT EXISTS(SELECT 1 FROM versiones_esquema WHERE version='010');
COMMIT;
