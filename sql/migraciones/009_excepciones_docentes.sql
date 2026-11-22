SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
SET SERVEROUTPUT ON
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM versiones_esquema WHERE version='008';
    IF n<>1 OR USER IN ('SYS','SYSTEM') THEN
        RAISE_APPLICATION_ERROR(-20310,'Se requiere 008 y el propietario del proyecto.');
    END IF;
    SELECT COUNT(*) INTO n FROM user_tab_columns
        WHERE table_name='VERIFICACION_ESTUDIANTES' AND column_name='AUTORIZADO_DOCENTE_POR';
    IF n=0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE verificacion_estudiantes ADD (
            autorizado_docente_por NUMBER CONSTRAINT fk_verificacion_docente REFERENCES profesores(profesor_id),
            materia_autorizacion_id NUMBER CONSTRAINT fk_verificacion_materia REFERENCES materias(materia_id))';
    END IF;
    SELECT COUNT(*) INTO n FROM user_constraints WHERE constraint_name='CK_VERIFICACION_APROBADA';
    IF n=1 THEN EXECUTE IMMEDIATE 'ALTER TABLE verificacion_estudiantes DROP CONSTRAINT ck_verificacion_aprobada'; END IF;
    EXECUTE IMMEDIATE 'ALTER TABLE verificacion_estudiantes ADD CONSTRAINT ck_verificacion_aprobada CHECK
        (excepcion_activa=0 OR (documento_huella IS NOT NULL AND tipo_documento IS NOT NULL AND
         documento_final IS NOT NULL AND clave_hash IS NOT NULL AND categoria IS NOT NULL AND
         referencia IS NOT NULL AND autorizado_en IS NOT NULL AND
         ((autorizado_por IS NOT NULL AND autorizado_docente_por IS NULL AND materia_autorizacion_id IS NULL) OR
          (autorizado_por IS NULL AND autorizado_docente_por IS NOT NULL AND materia_autorizacion_id IS NOT NULL))))';
END;
/
COMMENT ON COLUMN verificacion_estudiantes.autorizado_docente_por IS 'Docente que autoriza el acceso alternativo; no es una confirmacion de asistencia.';
COMMENT ON COLUMN verificacion_estudiantes.materia_autorizacion_id IS 'Materia propia con matricula vigente al emitir o renovar la credencial de acceso.';
@sql/37_paquete_excepciones_009.sql
@sql/38_paquete_excepciones_docentes.sql
BEGIN
    EXECUTE IMMEDIATE 'GRANT EXECUTE ON pkg_excepciones_docentes TO UPC_ROL_ADMIN';
EXCEPTION WHEN OTHERS THEN IF SQLCODE<>-1917 THEN RAISE; END IF;
END;
/
@sql/36_recompilar_esquema.sql
@sql/35_verificar_excepciones.sql
@sql/39_verificar_excepciones_docentes.sql
INSERT INTO versiones_esquema(version,descripcion)
SELECT '009','Autorizacion docente de excepciones con matricula, vigencia, version y entrega manual' FROM dual
WHERE NOT EXISTS(SELECT 1 FROM versiones_esquema WHERE version='009');
COMMIT;
