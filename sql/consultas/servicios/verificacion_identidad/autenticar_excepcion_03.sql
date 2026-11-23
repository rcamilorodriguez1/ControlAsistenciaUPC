SELECT e.estudiante_id,e.nombre,v.documento_final,v.clave_hash,v.version_credencial,
            CASE WHEN e.activo=1 AND v.excepcion_activa=1 AND
            (v.expira_en IS NULL OR v.expira_en>SYSTIMESTAMP) THEN 1 ELSE 0 END
            FROM verificacion_estudiantes v JOIN estudiantes e ON e.estudiante_id=v.estudiante_id
            WHERE v.documento_huella=:d
