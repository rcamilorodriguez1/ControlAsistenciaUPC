-- Solo se ejecuta desde instalar.sql DESPUES de verificar tablas, vistas y PL/SQL.
-- No utilizar este archivo para dar por terminada una instalacion parcial.
INSERT INTO versiones_esquema (version, descripcion)
VALUES ('001', 'Esquema inicial compatible con la aplicacion y presentacion SQL/PLSQL');
COMMIT;
PROMPT Version aplicada:
SELECT version, descripcion, aplicado_en FROM versiones_esquema ORDER BY version;
