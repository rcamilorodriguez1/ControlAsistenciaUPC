SELECT e.estudiante_id,e.nombre,v.documento_final,v.version_credencial,e.activo
FROM estudiantes e JOIN verificacion_estudiantes v ON v.estudiante_id=e.estudiante_id
WHERE v.documento_huella=:d
