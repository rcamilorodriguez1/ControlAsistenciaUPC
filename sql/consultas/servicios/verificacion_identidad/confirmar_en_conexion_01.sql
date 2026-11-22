SELECT version_credencial,clave_hash,excepcion_activa,
            CASE WHEN expira_en IS NULL OR expira_en>SYSTIMESTAMP THEN 1 ELSE 0 END
            FROM verificacion_estudiantes WHERE estudiante_id=:i FOR UPDATE WAIT 5