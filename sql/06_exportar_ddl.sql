-- Desde la raiz: cree antes exports desde CMD con mkdir exports.
-- Conectado como UPC_ASISTENCIA: @sql/06_exportar_ddl.sql
-- Exporta definiciones, no datos ni credenciales de la conexion.
-- Tablas primero; las FK se emiten como ALTER TABLE al terminar las tablas.
-- No fija el nombre del esquema original en el DDL generado.
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING OFF
SET PAGESIZE 0
SET LINESIZE 32767
SET LONG 2000000
SET LONGCHUNKSIZE 32767
SET TRIMSPOOL ON
SET SERVEROUTPUT OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
WHENEVER OSERROR EXIT FAILURE
BEGIN
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SQLTERMINATOR', TRUE);
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'SEGMENT_ATTRIBUTES', FALSE);
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'EMIT_SCHEMA', FALSE);
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'REF_CONSTRAINTS', FALSE);
END;
/
SET TERMOUT OFF
SPOOL exports/esquema_ddl.sql
PROMPT -- Exportacion de estructura. Conectar a un esquema nuevo antes de ejecutar.
PROMPT -- No incluye datos ni filas de VERSIONES_ESQUEMA. Para instalar la app use oracle_scripts.sql.
PROMPT WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
PROMPT WHENEVER OSERROR EXIT FAILURE
PROMPT SET DEFINE OFF
PROMPT -- 1. Tablas, claves primarias, unicidad y restricciones CHECK.
SELECT DBMS_METADATA.GET_DDL('TABLE', table_name) FROM user_tables ORDER BY table_name;
PROMPT -- 2. Claves foraneas: todas las tablas referenciadas ya existen.
SELECT DBMS_METADATA.GET_DDL('REF_CONSTRAINT', constraint_name) FROM user_constraints
WHERE constraint_type = 'R' ORDER BY table_name, constraint_name;
PROMPT -- 3. Indices adicionales; los de PK/UNIQUE ya se crearon con las tablas.
SELECT DBMS_METADATA.GET_DDL('INDEX', index_name) FROM user_indexes
WHERE generated = 'N' AND index_name NOT IN
    (SELECT index_name FROM user_constraints WHERE index_name IS NOT NULL)
ORDER BY index_name;
PROMPT -- 4. Comentarios de tablas y columnas para el diccionario y Data Modeler.
SELECT DBMS_METADATA.GET_DEPENDENT_DDL('COMMENT', table_name)
FROM user_tables
WHERE table_name IN (
    SELECT table_name FROM user_tab_comments WHERE comments IS NOT NULL
    UNION
    SELECT table_name FROM user_col_comments WHERE comments IS NOT NULL
)
ORDER BY table_name;
PROMPT -- 5. Vistas de consulta.
SELECT DBMS_METADATA.GET_DDL('VIEW', view_name) FROM user_views ORDER BY view_name;
PROMPT -- 6. Paquetes PL/SQL: contexto de auditoria antes del paquete que lo utiliza.
SELECT DBMS_METADATA.GET_DDL('PACKAGE', object_name) FROM user_objects WHERE object_type = 'PACKAGE'
ORDER BY CASE WHEN object_name = 'PKG_AUDITORIA' THEN 0 ELSE 1 END, object_name;
-- GET_DDL('PACKAGE') incluye especificacion y cuerpo; no duplicar PACKAGE_BODY.
PROMPT -- 7. Disparadores, despues de sus tablas y paquetes dependientes.
SELECT DBMS_METADATA.GET_DDL('TRIGGER', trigger_name) FROM user_triggers ORDER BY trigger_name;
SPOOL OFF
BEGIN
    DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM, 'DEFAULT', TRUE);
END;
/
SET TERMOUT ON
SET FEEDBACK ON
SET HEADING ON
SET PAGESIZE 100
PROMPT DDL exportado a exports/esquema_ddl.sql. Para instalar use los scripts versionados.
