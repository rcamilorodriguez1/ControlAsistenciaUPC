SELECT intentos,CASE WHEN bloqueado_hasta>SYSTIMESTAMP THEN 1 ELSE 0 END,
            CASE WHEN ventana_en<SYSTIMESTAMP-INTERVAL '15' MINUTE THEN 1 ELSE 0 END
            FROM limites_acceso WHERE clave=:c FOR UPDATE WAIT 5