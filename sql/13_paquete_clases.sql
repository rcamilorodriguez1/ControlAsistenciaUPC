-- Ninguna operacion hace COMMIT: la transaccion pertenece al cliente.
CREATE OR REPLACE PACKAGE pkg_clases AS
    PROCEDURE abrir_clase(p_materia_id NUMBER,p_fecha_hora TIMESTAMP WITH TIME ZONE,p_clase_id OUT NUMBER);
    PROCEDURE confirmar_clase(p_clase_id NUMBER,p_clave VARCHAR2,p_origen VARCHAR2,p_registros CLOB,p_cantidad OUT NUMBER);
    -- Compatibilidad de SQL 001/002: se llama desde el disparador al insertar sin CLASE_ID.
    FUNCTION clase_legada(p_materia_id NUMBER,p_fecha_hora TIMESTAMP WITH TIME ZONE) RETURN NUMBER;
END pkg_clases;
/
SHOW ERRORS PACKAGE pkg_clases
CREATE OR REPLACE PACKAGE BODY pkg_clases AS
    PROCEDURE exigir_profesor(p_materia NUMBER) IS
        v_profesor NUMBER;
    BEGIN
        IF pkg_auditoria.rol_actual<>'PROFESOR' OR pkg_auditoria.actor_actual IS NULL THEN
            RAISE_APPLICATION_ERROR(-20071,'Inicie sesion como profesor.');
        END IF;
        SELECT profesor_id INTO v_profesor FROM materias WHERE materia_id=p_materia FOR UPDATE;
        IF v_profesor<>pkg_auditoria.actor_actual THEN
            RAISE_APPLICATION_ERROR(-20072,'La materia no pertenece al profesor actual.');
        END IF;
    EXCEPTION WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20072,'La materia ya no existe.');
    END;

    PROCEDURE abrir_clase(p_materia_id NUMBER,p_fecha_hora TIMESTAMP WITH TIME ZONE,p_clase_id OUT NUMBER) IS
    BEGIN
        IF p_fecha_hora IS NULL THEN RAISE_APPLICATION_ERROR(-20073,'Indique fecha y hora de inicio de la clase.'); END IF;
        exigir_profesor(p_materia_id);
        BEGIN
            SELECT clase_id INTO p_clase_id FROM clases
            WHERE materia_id=p_materia_id AND instante_utc=SYS_EXTRACT_UTC(p_fecha_hora) AND lote_legado=0;
        EXCEPTION WHEN NO_DATA_FOUND THEN
            INSERT INTO clases(materia_id,profesor_id,fecha_hora)
            VALUES(p_materia_id,pkg_auditoria.actor_actual,p_fecha_hora) RETURNING clase_id INTO p_clase_id;
        END;
    END;

    FUNCTION clase_legada(p_materia_id NUMBER,p_fecha_hora TIMESTAMP WITH TIME ZONE) RETURN NUMBER IS
        v_id NUMBER;
        v_profesor NUMBER;
        v_origen clases.origen%TYPE;
    BEGIN
        SELECT profesor_id INTO v_profesor FROM materias WHERE materia_id=p_materia_id FOR UPDATE;
        BEGIN
            SELECT clase_id,origen INTO v_id,v_origen FROM clases
            WHERE materia_id=p_materia_id AND instante_utc=SYS_EXTRACT_UTC(p_fecha_hora) AND lote_legado=0;
            IF v_origen<>'LEGADO' THEN
                RAISE_APPLICATION_ERROR(-20074,'Use la clase seleccionada y su confirmacion; ese horario ya tiene una clase.');
            END IF;
        EXCEPTION WHEN NO_DATA_FOUND THEN
            INSERT INTO clases(materia_id,profesor_id,fecha_hora,estado,origen,confirmado_en)
            VALUES(p_materia_id,v_profesor,p_fecha_hora,'CONFIRMADA','LEGADO',SYSTIMESTAMP) RETURNING clase_id INTO v_id;
        END;
        RETURN v_id;
    END;

    PROCEDURE confirmar_clase(p_clase_id NUMBER,p_clave VARCHAR2,p_origen VARCHAR2,p_registros CLOB,p_cantidad OUT NUMBER) IS
        v_clase clases%ROWTYPE;
        v_array JSON_ARRAY_T;
        v_obj JSON_OBJECT_T;
        v_elemento JSON_ELEMENT_T;
        v_total NUMBER;
        v_matricula NUMBER;
        v_id NUMBER;
        v_detectado NUMBER;
        v_presente NUMBER;
        v_motivo VARCHAR2(32767);
        v_fecha TIMESTAMP WITH TIME ZONE;
        v_primera TIMESTAMP WITH TIME ZONE;
        v_tipo VARCHAR2(12) := UPPER(p_origen);
        TYPE ids_t IS TABLE OF BOOLEAN INDEX BY VARCHAR2(100);
        v_ids ids_t;
    BEGIN
        SAVEPOINT confirmar_clase_003;
        IF p_clave IS NULL OR NOT REGEXP_LIKE(p_clave,'^[a-f0-9]{32}$') OR v_tipo IS NULL OR v_tipo NOT IN ('FACIAL','VOZ') THEN
            RAISE_APPLICATION_ERROR(-20073,'Identificador de propuesta u origen invalido.');
        END IF;
        BEGIN
            SELECT * INTO v_clase FROM clases WHERE clase_id=p_clase_id;
        EXCEPTION WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20073,'La clase ya no existe.'); END;
        exigir_profesor(v_clase.materia_id);
        SELECT * INTO v_clase FROM clases WHERE clase_id=p_clase_id FOR UPDATE;
        IF v_clase.estado='CONFIRMADA' THEN
            IF v_clase.clave_confirmacion=p_clave AND v_clase.origen=v_tipo
                AND DBMS_LOB.COMPARE(v_clase.propuesta_confirmada,p_registros)=0 THEN
                p_cantidad:=v_clase.registros_confirmados;
                RETURN;
            END IF;
            RAISE_APPLICATION_ERROR(-20074,'La clase ya fue confirmada. Consulte sus registros; no se duplico la asistencia.');
        END IF;
        -- Evita altas/retiros concurrentes mientras se valida y escribe la lista completa.
        -- NOWAIT evita interbloqueos con transacciones de matricula ajenas.
        BEGIN
            LOCK TABLE materia_estudiantes IN SHARE MODE NOWAIT;
        EXCEPTION WHEN OTHERS THEN
            IF SQLCODE=-54 THEN RAISE_APPLICATION_ERROR(-20075,'Hay una matricula en curso. Espere y vuelva a revisar la clase.'); END IF;
            RAISE;
        END;
        v_array:=JSON_ARRAY_T.parse(p_registros);
        v_array.on_error(1);
        v_total:=v_array.get_size;
        SELECT COUNT(*) INTO v_matricula FROM materia_estudiantes WHERE materia_id=v_clase.materia_id;
        IF v_total=0 OR v_total<>v_matricula THEN
            RAISE_APPLICATION_ERROR(-20076,'La matricula cambio o la propuesta esta incompleta. Vuelva a analizar.');
        END IF;
        FOR i IN 0..v_total-1 LOOP
            v_elemento:=v_array.get(i);
            IF v_elemento IS NULL OR NOT v_elemento.is_object THEN RAISE_APPLICATION_ERROR(-20077,'Fila de asistencia invalida.'); END IF;
            v_obj:=TREAT(v_elemento AS JSON_OBJECT_T);
            v_obj.on_error(1);
            v_elemento:=v_obj.get('estudiante_id');
            IF v_elemento IS NULL OR NOT v_elemento.is_number THEN RAISE_APPLICATION_ERROR(-20077,'ID de estudiante invalido.'); END IF;
            v_id:=v_obj.get_number('estudiante_id');
            IF v_id<=0 OR TRUNC(v_id)<>v_id OR v_ids.EXISTS(TO_CHAR(v_id)) THEN
                RAISE_APPLICATION_ERROR(-20077,'Hay un estudiante duplicado o invalido.');
            END IF;
            v_ids(TO_CHAR(v_id)):=TRUE;
            SELECT COUNT(*) INTO v_matricula FROM materia_estudiantes WHERE materia_id=v_clase.materia_id AND estudiante_id=v_id;
            IF v_matricula<>1 THEN RAISE_APPLICATION_ERROR(-20076,'La matricula cambio. Vuelva a analizar.'); END IF;
            v_elemento:=v_obj.get('detectado');
            IF v_elemento IS NULL OR NOT v_elemento.is_number THEN RAISE_APPLICATION_ERROR(-20077,'Deteccion invalida.'); END IF;
            v_detectado:=v_obj.get_number('detectado');
            v_elemento:=v_obj.get('presente');
            IF v_elemento IS NULL OR NOT v_elemento.is_number THEN RAISE_APPLICATION_ERROR(-20077,'Presencia invalida.'); END IF;
            v_presente:=v_obj.get_number('presente');
            IF v_detectado NOT IN (0,1) OR v_presente NOT IN (0,1) THEN RAISE_APPLICATION_ERROR(-20077,'Presencia limitada a 0 o 1.'); END IF;
            v_motivo:=NULL;
            IF v_presente<>v_detectado THEN
                v_elemento:=v_obj.get('motivo');
                IF v_elemento IS NULL OR NOT v_elemento.is_string THEN RAISE_APPLICATION_ERROR(-20078,'Explique cada correccion manual.'); END IF;
                v_motivo:=TRIM(v_obj.get_string('motivo'));
                IF v_motivo IS NULL OR LENGTH(v_motivo)>500 THEN RAISE_APPLICATION_ERROR(-20078,'Cada correccion necesita un motivo de 1 a 500 caracteres.'); END IF;
            END IF;
            v_fecha:=TO_TIMESTAMP_TZ(v_obj.get_string('fecha_hora'),'YYYY-MM-DD"T"HH24:MI:SS.FF6TZH:TZM');
            IF v_fecha IS NULL THEN RAISE_APPLICATION_ERROR(-20077,'Fecha del analisis obligatoria.'); END IF;
            IF i=0 THEN v_primera:=v_fecha;
            ELSIF v_fecha<>v_primera THEN RAISE_APPLICATION_ERROR(-20077,'La propuesta mezcla fechas de analisis.'); END IF;
            INSERT INTO registros_asistencia(clase_id,materia_id,estudiante_id,fecha_hora,presente,presente_detectado,
                                            corregido_manual,motivo_correccion,revisado_por,revisado_en)
            VALUES(p_clase_id,v_clase.materia_id,v_id,v_fecha,v_presente,v_detectado,
                   CASE WHEN v_motivo IS NULL THEN 0 ELSE 1 END,v_motivo,
                   CASE WHEN v_motivo IS NOT NULL THEN pkg_auditoria.actor_actual END,
                   CASE WHEN v_motivo IS NOT NULL THEN SYSTIMESTAMP END);
        END LOOP;
        UPDATE clases SET estado='CONFIRMADA',origen=v_tipo,clave_confirmacion=p_clave,
            propuesta_confirmada=p_registros,confirmado_en=SYSTIMESTAMP,registros_confirmados=v_total
        WHERE clase_id=p_clase_id;
        p_cantidad:=v_total;
    EXCEPTION WHEN OTHERS THEN
        ROLLBACK TO confirmar_clase_003;
        RAISE;
    END;
END pkg_clases;
/
SHOW ERRORS PACKAGE BODY pkg_clases
