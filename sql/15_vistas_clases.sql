CREATE OR REPLACE VIEW v_clases AS
SELECT c.clase_id,c.materia_id,m.codigo_materia,m.nombre materia,c.profesor_id,
       c.fecha_hora,c.lote_legado,c.estado,c.origen,c.registros_confirmados,c.creado_en,c.confirmado_en
FROM clases c JOIN materias m ON m.materia_id=c.materia_id;
CREATE OR REPLACE VIEW v_registros_asistencia AS
SELECT ra.asistencia_id,ra.clase_id,ra.materia_id,m.codigo_materia,m.nombre materia,
       ra.estudiante_id,e.nombre estudiante,ra.fecha_hora,c.fecha_hora fecha_clase,
       ra.presente,CASE ra.presente WHEN 1 THEN 'PRESENTE' ELSE 'AUSENTE' END estado,
       ra.presente_detectado,ra.corregido_manual,ra.motivo_correccion,ra.revisado_por,ra.revisado_en,c.origen
FROM registros_asistencia ra JOIN clases c ON c.clase_id=ra.clase_id
JOIN materias m ON m.materia_id=ra.materia_id JOIN estudiantes e ON e.estudiante_id=ra.estudiante_id;
CREATE OR REPLACE VIEW v_resumen_materias AS
SELECT m.materia_id,m.codigo_materia,m.nombre,COUNT(ra.asistencia_id) registros,
       COUNT(DISTINCT c.clase_id) tomas_registradas,
       NVL(ROUND(AVG(ra.presente)*100,2),0) porcentaje_asistencia
FROM materias m LEFT JOIN clases c ON c.materia_id=m.materia_id AND c.estado='CONFIRMADA'
LEFT JOIN registros_asistencia ra ON ra.clase_id=c.clase_id
GROUP BY m.materia_id,m.codigo_materia,m.nombre;
CREATE OR REPLACE VIEW v_auditoria_asistencia AS
SELECT auditoria_id,operacion,asistencia_id,materia_anterior,estudiante_anterior,fecha_anterior,presente_anterior,
       materia_nueva,estudiante_nuevo,fecha_nueva,presente_nuevo,ocurrido_en,usuario_bd,actor_rol,actor_id,motivo,
       modulo,identificador_cliente,clase_anterior,clase_nueva,detectado_anterior,correccion_inicial,motivo_inicial,revisor_inicial
FROM auditoria_asistencia;
