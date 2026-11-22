
                SELECT COUNT(DISTINCT me.estudiante_id)
                FROM materia_estudiantes me
                JOIN materias m ON m.materia_id = me.materia_id
                JOIN estudiantes e ON e.estudiante_id=me.estudiante_id
                WHERE m.profesor_id = :profesor_id AND m.activo=1 AND e.activo=1
                