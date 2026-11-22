UPDATE limites_acceso SET intentos=:n,
                    ventana_en=CASE WHEN :exp=1 THEN SYSTIMESTAMP ELSE ventana_en END,
                    bloqueado_hasta=CASE WHEN :n>=5 THEN SYSTIMESTAMP+INTERVAL '15' MINUTE END WHERE clave=:c