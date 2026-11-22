
                SELECT m.materia_id,m.codigo_materia,m.nombre,m.seccion,m.profesor_id,
                       NVL(me.total,0) AS total_estudiantes,NVL(c.total,0) AS total_clases
                FROM materias m
                LEFT JOIN (SELECT materia_id,COUNT(*) total FROM materia_estudiantes GROUP BY materia_id) me
                       ON me.materia_id=m.materia_id
                LEFT JOIN (SELECT materia_id,COUNT(*) total FROM clases WHERE estado='CONFIRMADA' GROUP BY materia_id) c
                       ON c.materia_id=m.materia_id
                WHERE m.profesor_id=:profesor_id AND m.activo=1
                ORDER BY m.materia_id
                