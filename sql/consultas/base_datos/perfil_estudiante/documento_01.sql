SELECT v.tipo_documento,v.documento_final,NVL(v.version_credencial,0)
FROM estudiantes e LEFT JOIN verificacion_estudiantes v ON v.estudiante_id=e.estudiante_id
WHERE e.estudiante_id=:i AND e.activo=1
