CREATE OR REPLACE TRIGGER trg_asistencia_clase
BEFORE INSERT OR UPDATE ON registros_asistencia FOR EACH ROW
DECLARE
    v_estado clases.estado%TYPE;
    v_origen clases.origen%TYPE;
BEGIN
    IF INSERTING THEN
        IF :NEW.clase_id IS NULL THEN
            :NEW.clase_id:=pkg_clases.clase_legada(:NEW.materia_id,:NEW.fecha_hora);
        END IF;
        SELECT estado,origen INTO v_estado,v_origen FROM clases WHERE clase_id=:NEW.clase_id FOR UPDATE;
        IF v_estado='CONFIRMADA' AND v_origen<>'LEGADO' THEN
            RAISE_APPLICATION_ERROR(-20074,'La clase ya fue confirmada; no admite nuevos registros.');
        END IF;
        IF :NEW.presente_detectado IS NULL THEN :NEW.presente_detectado:=:NEW.presente; END IF;
        IF v_origen='LEGADO' THEN
            UPDATE clases SET registros_confirmados=registros_confirmados+1 WHERE clase_id=:NEW.clase_id;
        END IF;
    ELSIF :NEW.clase_id<>:OLD.clase_id OR :NEW.materia_id<>:OLD.materia_id
       OR :NEW.estudiante_id<>:OLD.estudiante_id OR :NEW.presente_detectado<>:OLD.presente_detectado
       OR :NEW.corregido_manual<>:OLD.corregido_manual
       OR NVL(:NEW.motivo_correccion,CHR(0))<>NVL(:OLD.motivo_correccion,CHR(0))
       OR NVL(:NEW.revisado_por,-1)<>NVL(:OLD.revisado_por,-1)
       OR (:NEW.revisado_en IS NULL AND :OLD.revisado_en IS NOT NULL)
       OR (:NEW.revisado_en IS NOT NULL AND :OLD.revisado_en IS NULL)
       OR :NEW.revisado_en<>:OLD.revisado_en THEN
        RAISE_APPLICATION_ERROR(-20079,'La identidad de clase y la revision inicial son inmutables. Corrija la presencia mediante el procedimiento auditable.');
    END IF;
END;
/
SHOW ERRORS TRIGGER trg_asistencia_clase

CREATE OR REPLACE TRIGGER trg_clases_identidad
BEFORE UPDATE ON clases FOR EACH ROW
BEGIN
    IF :OLD.estado='CONFIRMADA' AND (UPDATING('PROPUESTA_CONFIRMADA')
        OR (:OLD.origen<>'LEGADO' AND UPDATING('REGISTROS_CONFIRMADOS'))) THEN
        RAISE_APPLICATION_ERROR(-20079,'La confirmacion original y su cantidad son inmutables.');
    END IF;
    IF :NEW.materia_id<>:OLD.materia_id OR :NEW.profesor_id<>:OLD.profesor_id
       OR :NEW.fecha_hora<>:OLD.fecha_hora OR :NEW.lote_legado<>:OLD.lote_legado
       OR (:OLD.estado='CONFIRMADA' AND (
           :NEW.estado<>:OLD.estado OR :NEW.origen<>:OLD.origen
           OR NVL(:NEW.clave_confirmacion,CHR(0))<>NVL(:OLD.clave_confirmacion,CHR(0))
           OR :NEW.confirmado_en IS NULL OR :NEW.confirmado_en<>:OLD.confirmado_en)) THEN
        RAISE_APPLICATION_ERROR(-20079,'No cambie la identidad ni reabra una clase confirmada.');
    END IF;
END;
/
SHOW ERRORS TRIGGER trg_clases_identidad

-- Sustituye la version 002 para conservar clase y revision inicial en bajas/correcciones.
CREATE OR REPLACE TRIGGER trg_asistencia_aud
AFTER UPDATE OR DELETE ON registros_asistencia FOR EACH ROW
DECLARE
    v_operacion VARCHAR2(10);
BEGIN
    IF DELETING THEN v_operacion:='DELETE';
    ELSIF :OLD.presente<>:NEW.presente OR :OLD.fecha_hora<>:NEW.fecha_hora THEN v_operacion:='UPDATE';
    ELSE RETURN; END IF;
    INSERT INTO auditoria_asistencia(
        operacion,asistencia_id,materia_anterior,estudiante_anterior,fecha_anterior,presente_anterior,
        materia_nueva,estudiante_nuevo,fecha_nueva,presente_nuevo,clase_anterior,clase_nueva,
        detectado_anterior,correccion_inicial,motivo_inicial,revisor_inicial,
        usuario_bd,actor_rol,actor_id,motivo,modulo,identificador_cliente)
    VALUES(v_operacion,:OLD.asistencia_id,:OLD.materia_id,:OLD.estudiante_id,:OLD.fecha_hora,:OLD.presente,
        :NEW.materia_id,:NEW.estudiante_id,:NEW.fecha_hora,:NEW.presente,:OLD.clase_id,:NEW.clase_id,
        :OLD.presente_detectado,:OLD.corregido_manual,:OLD.motivo_correccion,:OLD.revisado_por,
        SYS_CONTEXT('USERENV','SESSION_USER'),pkg_auditoria.rol_actual,pkg_auditoria.actor_actual,
        pkg_auditoria.motivo_actual,SYS_CONTEXT('USERENV','MODULE'),SYS_CONTEXT('USERENV','CLIENT_IDENTIFIER'));
END;
/
SHOW ERRORS TRIGGER trg_asistencia_aud
