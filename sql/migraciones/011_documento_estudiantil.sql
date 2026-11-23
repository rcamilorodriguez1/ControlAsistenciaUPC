-- Conserva IDs, codigos anteriores, matriculas, resultados y autorizaciones existentes.
SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM versiones_esquema WHERE version='010';
    IF n<>1 OR USER IN ('SYS','SYSTEM') THEN RAISE_APPLICATION_ERROR(-20314,'Se requiere 010 y el propietario.'); END IF;
END;
/
@sql/41_paquete_gestion_documentos.sql
@sql/42_paquete_administracion_documentos.sql
@sql/43_paquete_excepciones_documentos.sql
@sql/44_paquete_excepciones_docentes_documentos.sql
@sql/36_recompilar_esquema.sql
@sql/45_verificar_documentos.sql
INSERT INTO versiones_esquema(version,descripcion)
SELECT '011','Documento estudiantil en registro, perfil y acceso; codigos anteriores conservados como legado' FROM dual
WHERE NOT EXISTS(SELECT 1 FROM versiones_esquema WHERE version='011');
COMMIT;
