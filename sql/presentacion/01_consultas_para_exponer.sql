-- UPC Aula / Base de Datos. Ejecucion manual como propietario del esquema.
-- Guion de SOLO LECTURA: no instala ni migra ni escribe datos de personas.
-- En SQL Developer: seleccionar una sentencia y F9.

-- 1. Conexion: usuario tecnico y esquema no son el rol del portal.
SELECT USER usuario_oracle, SYS_CONTEXT('USERENV','CURRENT_SCHEMA') esquema,
       SYS_CONTEXT('USERENV','CON_NAME') contenedor FROM dual;

-- 2. Evolucion: las migraciones conservan una version instalada.
SELECT version, descripcion FROM versiones_esquema ORDER BY version;

-- 3. Inventario de las catorce tablas, sin extraer sus filas.
SELECT table_name FROM user_tables ORDER BY table_name;

-- 4. Diccionario de columnas. NULLABLE describe si admite NULL.
SELECT table_name,column_id,column_name,data_type,nullable,identity_column
FROM user_tab_columns ORDER BY table_name,column_id;

-- 5. PK, UNIQUE, CHECK y FK. No confundir una FK con una referencia logica.
SELECT table_name,constraint_name,constraint_type,status,validated
FROM user_constraints ORDER BY table_name,constraint_type,constraint_name;

-- 6. Las once FK, con todas las columnas de la clave compuesta.
SELECT c.constraint_name,c.table_name tabla_hija,cc.column_name columna_hija,
       r.table_name tabla_padre,rc.column_name columna_padre,c.delete_rule
FROM user_constraints c
JOIN user_cons_columns cc ON cc.constraint_name=c.constraint_name
JOIN user_constraints r ON r.constraint_name=c.r_constraint_name
JOIN user_cons_columns rc ON rc.constraint_name=r.constraint_name AND rc.position=cc.position
WHERE c.constraint_type='R' ORDER BY c.constraint_name,cc.position;

-- 7. Relacion N:M: resumen por materia, incluyendo materias sin alumnos.
SELECT m.materia_id,m.codigo_materia,m.nombre,COUNT(me.estudiante_id) matriculas
FROM materias m LEFT JOIN materia_estudiantes me ON me.materia_id=m.materia_id
GROUP BY m.materia_id,m.codigo_materia,m.nombre ORDER BY m.nombre;

-- 8. Cada clase tiene estado propio. Un borrador no confirma presencia.
SELECT c.clase_id,m.codigo_materia,c.fecha_hora,c.estado,c.registros_confirmados
FROM clases c JOIN materias m ON m.materia_id=c.materia_id
ORDER BY c.fecha_hora DESC;

-- 9. JOIN y agregados: resultados confirmados por clase, sin nombres personales.
SELECT c.clase_id,m.codigo_materia,COUNT(*) decisiones,
       SUM(r.presente) presentes,SUM(1-r.presente) ausentes,
       ROUND(100*AVG(r.presente),2) porcentaje
FROM clases c JOIN materias m ON m.materia_id=c.materia_id
JOIN registros_asistencia r ON r.clase_id=c.clase_id AND r.materia_id=c.materia_id
WHERE c.estado='CONFIRMADA'
GROUP BY c.clase_id,m.codigo_materia ORDER BY c.clase_id;

-- 10. Duplicados: debe devolver cero filas.
SELECT clase_id,estudiante_id,COUNT(*) repeticiones
FROM registros_asistencia GROUP BY clase_id,estudiante_id HAVING COUNT(*)>1;

-- 11. Vistas: consultas almacenadas, no modelos graficos.
SELECT view_name FROM user_views ORDER BY view_name;

-- 12. Paquetes y cuerpos: ocho pares compilados.
SELECT object_name,object_type,status FROM user_objects
WHERE object_type IN ('PACKAGE','PACKAGE BODY') ORDER BY object_name,object_type;

-- 13. Rutinas publicas del esquema, sin ejecutar procedimientos de escritura.
SELECT object_name,procedure_name FROM user_procedures
WHERE object_type='PACKAGE' AND procedure_name IS NOT NULL
ORDER BY object_name,procedure_name;

-- 14. Los diez triggers y sus eventos.
SELECT trigger_name,table_name,trigger_type,triggering_event,status
FROM user_triggers ORDER BY table_name,trigger_name;

-- 15. Auditoria agregada: no mostrar motivos ni datos individuales al publico.
SELECT operacion,COUNT(*) eventos FROM auditoria_asistencia GROUP BY operacion;
SELECT accion,COUNT(*) eventos FROM eventos_gestion GROUP BY accion ORDER BY accion;

-- 16. Compilacion: las dos consultas deben devolver cero filas.
SELECT object_name,object_type,status FROM user_objects WHERE status<>'VALID';
SELECT name,type,line,position,text FROM user_errors WHERE attribute='ERROR';
