
                SELECT es.estudiante_id, es.nombre, es.embedding_facial, es.embedding_voz
                FROM materia_estudiantes me
                JOIN estudiantes es ON es.estudiante_id = me.estudiante_id
                WHERE me.materia_id = :materia_id AND es.activo=1
                ORDER BY es.nombre
                