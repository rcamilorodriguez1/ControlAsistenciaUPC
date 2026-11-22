UPDATE verificacion_estudiantes SET estado_verificacion=:e,verificado_en=SYSTIMESTAMP,
            factores_verificados=:f,factores_requeridos=:r,version_credencial=version_credencial+1
            WHERE estudiante_id=:i