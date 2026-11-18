-- Auditoria transaccional: sin COMMIT, sin transacciones autonomas, sin consultas a tablas mutantes.
CREATE OR REPLACE TRIGGER trg_asistencia_aud
AFTER UPDATE OR DELETE ON registros_asistencia
FOR EACH ROW
DECLARE
    v_operacion VARCHAR2(10);
BEGIN
    IF DELETING THEN
        v_operacion := 'DELETE';
    ELSIF :OLD.presente <> :NEW.presente
       OR :OLD.materia_id <> :NEW.materia_id
       OR :OLD.estudiante_id <> :NEW.estudiante_id
       OR :OLD.fecha_hora <> :NEW.fecha_hora THEN
        v_operacion := 'UPDATE';
    ELSE
        RETURN;
    END IF;
    INSERT INTO auditoria_asistencia (
        operacion, asistencia_id, materia_anterior, estudiante_anterior, fecha_anterior, presente_anterior,
        materia_nueva, estudiante_nuevo, fecha_nueva, presente_nuevo,
        usuario_bd, actor_rol, actor_id, motivo, modulo, identificador_cliente
    ) VALUES (
        v_operacion, :OLD.asistencia_id, :OLD.materia_id, :OLD.estudiante_id, :OLD.fecha_hora, :OLD.presente,
        :NEW.materia_id, :NEW.estudiante_id, :NEW.fecha_hora, :NEW.presente,
        SYS_CONTEXT('USERENV', 'SESSION_USER'), pkg_auditoria.rol_actual,
        pkg_auditoria.actor_actual, pkg_auditoria.motivo_actual,
        SYS_CONTEXT('USERENV', 'MODULE'), SYS_CONTEXT('USERENV', 'CLIENT_IDENTIFIER')
    );
END;
/
SHOW ERRORS TRIGGER trg_asistencia_aud

CREATE OR REPLACE TRIGGER trg_matriculas_hist
AFTER INSERT OR DELETE ON materia_estudiantes
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        INSERT INTO historial_matriculas (
            accion, materia_id, estudiante_id, matriculado_en,
            usuario_bd, actor_rol, actor_id, motivo, modulo, identificador_cliente
        ) VALUES (
            'ALTA', :NEW.materia_id, :NEW.estudiante_id, :NEW.matriculado_en,
            SYS_CONTEXT('USERENV', 'SESSION_USER'), pkg_auditoria.rol_actual,
            pkg_auditoria.actor_actual, pkg_auditoria.motivo_actual,
            SYS_CONTEXT('USERENV', 'MODULE'), SYS_CONTEXT('USERENV', 'CLIENT_IDENTIFIER')
        );
    ELSE
        INSERT INTO historial_matriculas (
            accion, materia_id, estudiante_id, matriculado_en,
            usuario_bd, actor_rol, actor_id, motivo, modulo, identificador_cliente
        ) VALUES (
            'RETIRO', :OLD.materia_id, :OLD.estudiante_id, :OLD.matriculado_en,
            SYS_CONTEXT('USERENV', 'SESSION_USER'), pkg_auditoria.rol_actual,
            pkg_auditoria.actor_actual, pkg_auditoria.motivo_actual,
            SYS_CONTEXT('USERENV', 'MODULE'), SYS_CONTEXT('USERENV', 'CLIENT_IDENTIFIER')
        );
    END IF;
END;
/
SHOW ERRORS TRIGGER trg_matriculas_hist

CREATE OR REPLACE TRIGGER trg_profesores_actualizado
BEFORE UPDATE ON profesores FOR EACH ROW
BEGIN :NEW.actualizado_en := SYSTIMESTAMP; END;
/
SHOW ERRORS TRIGGER trg_profesores_actualizado
CREATE OR REPLACE TRIGGER trg_estudiantes_actualizado
BEFORE UPDATE ON estudiantes FOR EACH ROW
BEGIN :NEW.actualizado_en := SYSTIMESTAMP; END;
/
SHOW ERRORS TRIGGER trg_estudiantes_actualizado
CREATE OR REPLACE TRIGGER trg_materias_actualizado
BEFORE UPDATE ON materias FOR EACH ROW
BEGIN :NEW.actualizado_en := SYSTIMESTAMP; END;
/
SHOW ERRORS TRIGGER trg_materias_actualizado

CREATE OR REPLACE VIEW v_auditoria_asistencia AS
SELECT auditoria_id, operacion, asistencia_id,
       materia_anterior, estudiante_anterior, fecha_anterior, presente_anterior,
       materia_nueva, estudiante_nuevo, fecha_nueva, presente_nuevo,
       ocurrido_en, usuario_bd, actor_rol, actor_id, motivo, modulo, identificador_cliente
FROM auditoria_asistencia;
CREATE OR REPLACE VIEW v_historial_matriculas AS
SELECT historial_id, accion, materia_id, estudiante_id, matriculado_en,
       ocurrido_en, usuario_bd, actor_rol, actor_id, motivo, modulo, identificador_cliente
FROM historial_matriculas;
