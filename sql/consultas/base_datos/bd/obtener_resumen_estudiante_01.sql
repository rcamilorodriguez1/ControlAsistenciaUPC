SELECT COUNT(*) FROM materia_estudiantes me JOIN materias m ON m.materia_id=me.materia_id
                   WHERE me.estudiante_id=:estudiante_id AND m.activo=1