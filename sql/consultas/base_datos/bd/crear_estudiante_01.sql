
                INSERT INTO estudiantes (nombre, codigo_institucional, embedding_facial, embedding_voz)
                VALUES (:nombre, :codigo_institucional, :embedding_facial, :embedding_voz)
                RETURNING estudiante_id INTO :out_id
                