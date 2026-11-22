
                SELECT COUNT(*), SUM(CASE WHEN presente = 1 THEN 1 ELSE 0 END)
                FROM registros_asistencia
                WHERE estudiante_id = :estudiante_id
                