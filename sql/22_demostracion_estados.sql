-- Laboratorio 004: fallo no confirmable, sin muestra requiere revision. Todo termina en rollback.
SET SERVEROUTPUT ON
SET DEFINE OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE
    v_profesor NUMBER;
    v_estudiante NUMBER;
    v_materia NUMBER;
    v_clase NUMBER;
    v_n NUMBER;
    v_clave VARCHAR2(32):=LOWER(RAWTOHEX(SYS_GUID()));
    v_codigo VARCHAR2(50):='DEMO_004_'||SUBSTR(v_clave,1,16);
    v_carga CLOB;
BEGIN
    SAVEPOINT laboratorio_estados;
    INSERT INTO profesores(usuario,contrasena,nombre) VALUES(v_codigo,'FIXTURE_NO_UTILIZABLE','Profesor laboratorio') RETURNING profesor_id INTO v_profesor;
    INSERT INTO estudiantes(nombre) VALUES('Estudiante sin muestra') RETURNING estudiante_id INTO v_estudiante;
    INSERT INTO materias(codigo_materia,nombre,profesor_id) VALUES(v_codigo,'Estados de deteccion',v_profesor) RETURNING materia_id INTO v_materia;
    pkg_auditoria.establecer_contexto('PROFESOR',v_profesor,'Laboratorio 004');
    pkg_asistencia.matricular_estudiante(v_estudiante,v_materia);
    pkg_clases.abrir_clase(v_materia,SYSTIMESTAMP,v_clase);
    v_carga:='[{"estudiante_id":'||v_estudiante||',"detectado":null,"estado_deteccion":"ANALISIS_FALLIDO","presente":0,"motivo":"No se permite","fecha_hora":"2026-11-11T10:00:00.000000-05:00"}]';
    BEGIN
        pkg_clases.confirmar_clase(v_clase,v_clave,'VOZ',v_carga,v_n);
        RAISE_APPLICATION_ERROR(-20090,'Se confirmo un analisis fallido.');
    EXCEPTION WHEN OTHERS THEN
        IF SQLCODE<>-20077 THEN RAISE; END IF;
        DBMS_OUTPUT.PUT_LINE('Analisis fallido: rechazado, ninguna ausencia guardada.');
    END;
    v_carga:='[{"estudiante_id":'||v_estudiante||',"detectado":null,"estado_deteccion":"SIN_MUESTRA","presente":0,"motivo":null,"fecha_hora":"2026-11-11T10:00:00.000000-05:00"}]';
    BEGIN
        pkg_clases.confirmar_clase(v_clase,v_clave,'VOZ',v_carga,v_n);
        RAISE_APPLICATION_ERROR(-20090,'Se resolvio sin muestra automaticamente.');
    EXCEPTION WHEN OTHERS THEN
        IF SQLCODE<>-20078 THEN RAISE; END IF;
        DBMS_OUTPUT.PUT_LINE('Sin muestra sin motivo: rechazado, decision manual obligatoria.');
    END;
    v_carga:=REPLACE(v_carga,'"motivo":null','"motivo":"Lista comprobada manualmente"');
    pkg_clases.confirmar_clase(v_clase,v_clave,'VOZ',v_carga,v_n);
    FOR r IN (SELECT estado_deteccion,presente_detectado,presente,corregido_manual,revisado_por
              FROM registros_asistencia WHERE clase_id=v_clase) LOOP
        DBMS_OUTPUT.PUT_LINE('Original='||r.estado_deteccion||' detectado='||NVL(TO_CHAR(r.presente_detectado),'NULL')||
            ' decision='||r.presente||' manual='||r.corregido_manual||' autor='||r.revisado_por);
    END LOOP;
    ROLLBACK TO laboratorio_estados;
    pkg_auditoria.limpiar_contexto;
    DBMS_OUTPUT.PUT_LINE('Rollback final: no quedan datos del laboratorio.');
EXCEPTION WHEN OTHERS THEN
    ROLLBACK TO laboratorio_estados;
    pkg_auditoria.limpiar_contexto;
    RAISE;
END;
/
