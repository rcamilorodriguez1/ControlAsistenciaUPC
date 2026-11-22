
                INSERT INTO profesores (usuario, contrasena, nombre)
                VALUES (:usuario, :contrasena, :nombre)
                RETURNING profesor_id INTO :out_id
                