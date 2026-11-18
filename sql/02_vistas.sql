-- Vistas de presentacion con columnas explicitas, sin hashes ni vectores biometricos.
CREATE OR REPLACE VIEW v_profesores AS
SELECT profesor_id, usuario, nombre, creado_en FROM profesores;
CREATE OR REPLACE VIEW v_estudiantes AS
SELECT estudiante_id, nombre, creado_en,
       CASE WHEN embedding_facial IS NOT NULL THEN 'SI' ELSE 'NO' END AS tiene_rostro,
       CASE WHEN embedding_voz IS NOT NULL THEN 'SI' ELSE 'NO' END AS tiene_voz
FROM estudiantes;
CREATE OR REPLACE VIEW v_materias AS
SELECT m.materia_id, m.codigo_materia, m.nombre, m.seccion,
       m.profesor_id, p.nombre AS profesor, m.creado_en
FROM materias m JOIN profesores p ON p.profesor_id = m.profesor_id;
CREATE OR REPLACE VIEW v_materia_estudiantes AS
SELECT me.materia_id, m.codigo_materia, m.nombre AS materia,
       me.estudiante_id, e.nombre AS estudiante, me.matriculado_en
FROM materia_estudiantes me
JOIN materias m ON m.materia_id = me.materia_id
JOIN estudiantes e ON e.estudiante_id = me.estudiante_id;
CREATE OR REPLACE VIEW v_registros_asistencia AS
SELECT ra.asistencia_id, ra.materia_id, m.codigo_materia, m.nombre AS materia,
       ra.estudiante_id, e.nombre AS estudiante, ra.fecha_hora, ra.presente,
       CASE ra.presente WHEN 1 THEN 'PRESENTE' ELSE 'AUSENTE' END AS estado
FROM registros_asistencia ra
JOIN materias m ON m.materia_id = ra.materia_id
JOIN estudiantes e ON e.estudiante_id = ra.estudiante_id;
CREATE OR REPLACE VIEW v_resumen_materias AS
SELECT m.materia_id, m.codigo_materia, m.nombre,
       COUNT(ra.asistencia_id) AS registros,
       COUNT(DISTINCT ra.fecha_hora) AS tomas_registradas,
       NVL(ROUND(AVG(ra.presente) * 100, 2), 0) AS porcentaje_asistencia
FROM materias m LEFT JOIN registros_asistencia ra ON ra.materia_id = m.materia_id
GROUP BY m.materia_id, m.codigo_materia, m.nombre;
CREATE OR REPLACE VIEW v_versiones_esquema AS
SELECT version, descripcion, aplicado_en FROM versiones_esquema;
