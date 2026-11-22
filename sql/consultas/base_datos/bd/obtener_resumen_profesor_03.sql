
                SELECT ROUND(AVG(CASE WHEN ra.presente = 1 THEN 100 ELSE 0 END))
                FROM registros_asistencia ra
                JOIN materias m ON m.materia_id = ra.materia_id
                WHERE m.profesor_id = :profesor_id
                