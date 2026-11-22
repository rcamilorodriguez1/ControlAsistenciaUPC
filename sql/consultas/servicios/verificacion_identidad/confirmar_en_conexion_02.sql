SELECT activo,CASE WHEN embedding_facial IS NOT NULL THEN 1 ELSE 0 END
            FROM estudiantes WHERE estudiante_id=:i FOR UPDATE WAIT 5