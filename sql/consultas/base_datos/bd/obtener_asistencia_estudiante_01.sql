
                SELECT ra.materia_id,ra.clase_id,ra.estudiante_id,
                       TO_CHAR(ra.fecha_hora, 'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') AS fecha_hora,
                       TO_CHAR(c.fecha_hora, 'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') AS fecha_clase,
                       ra.presente,ra.estado_deteccion
                FROM registros_asistencia ra JOIN clases c ON c.clase_id=ra.clase_id
                WHERE ra.estudiante_id = :estudiante_id
                