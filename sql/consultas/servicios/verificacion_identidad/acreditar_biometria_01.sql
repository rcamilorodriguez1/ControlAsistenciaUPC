SELECT e.activo,CASE WHEN e.embedding_facial IS NOT NULL THEN 1 ELSE 0 END,
            NVL(v.version_credencial,0) FROM estudiantes e LEFT JOIN verificacion_estudiantes v
            ON v.estudiante_id=e.estudiante_id WHERE e.estudiante_id=:i