-- SOLO LECTURA. Ejecutar cada SELECT con F9 y completar sus variables enlazadas.
-- Elegir IDs de materias/clases del entorno que el equipo haya decidido mostrar.

-- Clases de una materia, con su docente propietario.
SELECT c.clase_id,c.fecha_hora,c.estado,c.origen,c.registros_confirmados
FROM clases c JOIN materias m ON m.materia_id=c.materia_id
WHERE c.materia_id=:materia_id AND m.profesor_id=:profesor_id
ORDER BY c.fecha_hora DESC;

-- Agregado de una clase, sin datos identificables del alumno.
SELECT r.clase_id,r.estado_deteccion,r.presente,COUNT(*) estudiantes
FROM registros_asistencia r
WHERE r.clase_id=:clase_id
GROUP BY r.clase_id,r.estado_deteccion,r.presente ORDER BY r.estado_deteccion;

-- Cobertura de una materia: distintas clases registradas y resultados asociados.
SELECT m.materia_id,m.codigo_materia,COUNT(DISTINCT c.clase_id) clases,
       COUNT(r.asistencia_id) resultados
FROM materias m LEFT JOIN clases c ON c.materia_id=m.materia_id
LEFT JOIN registros_asistencia r ON r.clase_id=c.clase_id AND r.materia_id=c.materia_id
WHERE m.materia_id=:materia_id GROUP BY m.materia_id,m.codigo_materia;

-- Restricciones y sus columnas para la tabla elegida, por ejemplo CLASES.
SELECT c.constraint_name,c.constraint_type,cc.column_name,cc.position
FROM user_constraints c LEFT JOIN user_cons_columns cc ON cc.constraint_name=c.constraint_name
WHERE c.table_name=UPPER(:tabla) ORDER BY c.constraint_name,cc.position;

-- Firma publica de una rutina; por ejemplo PKG_CLASES / CONFIRMAR_CLASE.
SELECT package_name,object_name,argument_name,position,in_out,data_type
FROM user_arguments WHERE package_name=UPPER(:paquete) AND object_name=UPPER(:rutina)
ORDER BY overload,sequence;
