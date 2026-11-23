SELECT e.estudiante_id,e.nombre,v.tipo_documento,v.documento_final,e.embedding_facial,e.embedding_voz
FROM estudiantes e LEFT JOIN verificacion_estudiantes v ON v.estudiante_id=e.estudiante_id WHERE e.activo=1
