
                SELECT TO_CHAR(ra.fecha_hora, 'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') AS fecha_hora,
                       TO_CHAR(c.fecha_hora, 'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') AS fecha_clase,
                       ra.clase_id,c.origen,c.lote_legado,ra.presente,ra.corregido_manual,ra.estado_deteccion,
                       m.nombre AS materia_nombre, m.codigo_materia AS codigo_materia
                FROM registros_asistencia ra
                JOIN materias m ON m.materia_id = ra.materia_id
                JOIN clases c ON c.clase_id=ra.clase_id
                WHERE m.profesor_id = :profesor_id
                ORDER BY ra.fecha_hora DESC
                