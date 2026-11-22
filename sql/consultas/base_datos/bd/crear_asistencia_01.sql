
                INSERT INTO registros_asistencia (materia_id, estudiante_id, fecha_hora, presente)
                VALUES (:materia_id, :estudiante_id,
                        TO_TIMESTAMP_TZ(:fecha_hora, 'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM'),
                        :presente)
                