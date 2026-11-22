SELECT c.clase_id,c.materia_id,c.estado,c.origen,c.lote_legado,c.registros_confirmados,
                TO_CHAR(c.fecha_hora,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') fecha_hora
                FROM clases c JOIN materias m ON m.materia_id=c.materia_id
                WHERE c.materia_id=:m AND m.profesor_id=:p ORDER BY c.fecha_hora DESC,c.clase_id DESC