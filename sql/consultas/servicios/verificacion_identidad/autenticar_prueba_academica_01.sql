SELECT e.estudiante_id,e.nombre,e.codigo_institucional,NVL(v.version_credencial,0),e.activo
FROM estudiantes e LEFT JOIN verificacion_estudiantes v ON v.estudiante_id=e.estudiante_id
WHERE UPPER(TRIM(e.codigo_institucional))=:c
