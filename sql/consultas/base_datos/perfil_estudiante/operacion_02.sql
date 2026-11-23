
                WITH asistencias AS (
                    SELECT r.estudiante_id, r.materia_id, r.clase_id, r.presente,
                           c.fecha_hora, r.corregido_manual
                    FROM registros_asistencia r JOIN clases c ON c.clase_id=r.clase_id
                    WHERE r.estudiante_id=:estudiante_id AND c.estado='CONFIRMADA'
                ), mis_materias AS (
                    SELECT materia_id FROM materia_estudiantes WHERE estudiante_id=:estudiante_id
                    UNION
                    SELECT materia_id FROM asistencias
                )
                SELECT e.estudiante_id, e.nombre AS nombre_estudiante, v.tipo_documento,v.documento_final,
                       NVL(v.estado_verificacion,'PENDIENTE') estado_verificacion,
                       m.materia_id, m.nombre AS nombre_materia, m.codigo_materia, m.seccion,
                       CASE WHEN me.estudiante_id IS NOT NULL AND m.activo=1 THEN 1 ELSE 0 END matriculada,
                       a.clase_id, a.presente, a.corregido_manual,
                       TO_CHAR(a.fecha_hora,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') fecha_clase
                FROM estudiantes e
                LEFT JOIN verificacion_estudiantes v ON v.estudiante_id=e.estudiante_id
                LEFT JOIN mis_materias mm ON 1=1
                LEFT JOIN materias m ON m.materia_id=mm.materia_id
                LEFT JOIN materia_estudiantes me ON me.estudiante_id=e.estudiante_id AND me.materia_id=m.materia_id
                LEFT JOIN asistencias a ON a.materia_id=m.materia_id AND a.estudiante_id=e.estudiante_id
                WHERE e.estudiante_id=:estudiante_id AND e.activo=1
                ORDER BY matriculada DESC, m.nombre, m.materia_id, a.fecha_hora, a.clase_id
