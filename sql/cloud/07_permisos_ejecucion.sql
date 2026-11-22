-- Como propietario UPC_ASISTENCIA, despues de 001-008 y de crear UPC_AULA_APP.
-- Sin roles, ANY, DDL, cuotas, WITH GRANT OPTION ni DML sobre auditorias historicas.
SET DEFINE OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE n NUMBER;
BEGIN
    IF SYS_CONTEXT('USERENV','SESSION_USER') <> 'UPC_ASISTENCIA' THEN
        RAISE_APPLICATION_ERROR(-20411,'Conectar como propietario UPC_ASISTENCIA.');
    END IF;
    SELECT COUNT(*) INTO n FROM versiones_esquema WHERE version='008';
    IF n <> 1 THEN RAISE_APPLICATION_ERROR(-20411,'Verificar 001-008 primero.'); END IF;
END;
/
GRANT SELECT ON profesores TO UPC_AULA_APP;
GRANT INSERT (usuario,contrasena,nombre) ON profesores TO UPC_AULA_APP;
GRANT UPDATE (contrasena) ON profesores TO UPC_AULA_APP;
GRANT SELECT ON estudiantes TO UPC_AULA_APP;
GRANT INSERT (nombre,codigo_institucional,embedding_facial,embedding_voz) ON estudiantes TO UPC_AULA_APP;
GRANT SELECT ON materias TO UPC_AULA_APP;
GRANT SELECT ON materia_estudiantes TO UPC_AULA_APP;
GRANT SELECT ON clases TO UPC_AULA_APP;
GRANT SELECT ON registros_asistencia TO UPC_AULA_APP;
GRANT INSERT (materia_id,estudiante_id,fecha_hora,presente) ON registros_asistencia TO UPC_AULA_APP;
GRANT SELECT ON administradores TO UPC_AULA_APP;
GRANT SELECT ON verificacion_estudiantes TO UPC_AULA_APP;
GRANT INSERT (estudiante_id) ON verificacion_estudiantes TO UPC_AULA_APP;
GRANT UPDATE (estado_verificacion,verificado_en,factores_verificados,factores_requeridos,version_credencial)
    ON verificacion_estudiantes TO UPC_AULA_APP;
GRANT SELECT ON sesiones_usuario TO UPC_AULA_APP;
GRANT INSERT (rol,actor_id,token_hash,creada_en,actividad_en,expira_en,revocada_en)
    ON sesiones_usuario TO UPC_AULA_APP;
GRANT UPDATE (revocada_en) ON sesiones_usuario TO UPC_AULA_APP;
GRANT SELECT ON limites_acceso TO UPC_AULA_APP;
GRANT INSERT (clave) ON limites_acceso TO UPC_AULA_APP;
GRANT UPDATE (intentos,ventana_en,bloqueado_hasta) ON limites_acceso TO UPC_AULA_APP;
GRANT DELETE ON limites_acceso TO UPC_AULA_APP;
GRANT INSERT (entidad,entidad_id,accion,motivo,actor_rol,actor_id) ON eventos_gestion TO UPC_AULA_APP;
GRANT SELECT ON versiones_esquema TO UPC_AULA_APP;
GRANT EXECUTE ON pkg_auditoria TO UPC_AULA_APP;
GRANT EXECUTE ON pkg_asistencia TO UPC_AULA_APP;
GRANT EXECUTE ON pkg_clases TO UPC_AULA_APP;
GRANT EXECUTE ON pkg_gestion TO UPC_AULA_APP;
GRANT EXECUTE ON pkg_sesiones TO UPC_AULA_APP;
