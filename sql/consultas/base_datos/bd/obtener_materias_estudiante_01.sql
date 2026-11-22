
                SELECT m.materia_id, m.codigo_materia, m.nombre, m.seccion, m.profesor_id
                FROM materia_estudiantes me
                JOIN materias m ON m.materia_id = me.materia_id
                WHERE me.estudiante_id = :estudiante_id AND m.activo=1
                ORDER BY m.materia_id
                