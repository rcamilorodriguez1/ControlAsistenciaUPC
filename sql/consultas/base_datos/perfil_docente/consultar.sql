SELECT p.profesor_id,p.nombre nombre_profesor,p.usuario,
       m.materia_id,m.nombre nombre_materia,m.codigo_materia,m.seccion,m.activo materia_activa,
       (SELECT COUNT(*) FROM materia_estudiantes me JOIN estudiantes e ON e.estudiante_id=me.estudiante_id
        WHERE me.materia_id=m.materia_id AND e.activo=1) total_estudiantes,
       c.clase_id,c.estado,
       TO_CHAR(c.fecha_hora,'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM') fecha_clase
FROM profesores p
LEFT JOIN materias m ON m.profesor_id=p.profesor_id
LEFT JOIN clases c ON c.materia_id=m.materia_id
WHERE p.profesor_id=:profesor_id AND p.activo=1
ORDER BY m.activo DESC,m.nombre,m.materia_id,c.fecha_hora,c.clase_id
