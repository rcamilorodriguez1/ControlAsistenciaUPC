-- Laboratorio transaccional: no deja personas, clases, asistencias ni historial.
SET SERVEROUTPUT ON
SET DEFINE OFF
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE
    v_profesor NUMBER;
    v_estudiante NUMBER;
    v_materia NUMBER;
    v_clase NUMBER;
    v_repetida NUMBER;
    v_cantidad NUMBER;
    v_clave VARCHAR2(32):=LOWER(RAWTOHEX(SYS_GUID()));
    v_codigo VARCHAR2(50):='DEMO_003_'||SUBSTR(v_clave,1,16);
    v_carga CLOB;
BEGIN
    SAVEPOINT laboratorio_clases;
    INSERT INTO profesores(usuario,contrasena,nombre) VALUES(v_codigo,'FIXTURE_NO_UTILIZABLE','Profesor de laboratorio') RETURNING profesor_id INTO v_profesor;
    INSERT INTO estudiantes(nombre) VALUES('Estudiante de laboratorio') RETURNING estudiante_id INTO v_estudiante;
    INSERT INTO materias(codigo_materia,nombre,profesor_id) VALUES(v_codigo,'Clase de laboratorio',v_profesor) RETURNING materia_id INTO v_materia;
    pkg_auditoria.establecer_contexto('PROFESOR',v_profesor,'Laboratorio 003');
    pkg_asistencia.matricular_estudiante(v_estudiante,v_materia);
    pkg_clases.abrir_clase(v_materia,TIMESTAMP '2026-11-11 08:00:00 -05:00',v_clase);
    pkg_clases.abrir_clase(v_materia,TIMESTAMP '2026-11-11 13:00:00 +00:00',v_repetida);
    IF v_clase<>v_repetida THEN RAISE_APPLICATION_ERROR(-20090,'Se duplico la clase.'); END IF;
    DBMS_OUTPUT.PUT_LINE('Mismo horario con distinto offset: misma clase.');
    v_carga:='[{"estudiante_id":'||v_estudiante||',"detectado":0,"presente":1,"motivo":"Presencia comprobada manualmente","fecha_hora":"2026-11-11T08:15:00.123456-05:00"}]';
    pkg_clases.confirmar_clase(v_clase,v_clave,'FACIAL',v_carga,v_cantidad);
    DBMS_OUTPUT.PUT_LINE('Confirmados: '||v_cantidad||'. Correccion y autor guardados.');
    pkg_clases.confirmar_clase(v_clase,v_clave,'FACIAL',v_carga,v_cantidad);
    DBMS_OUTPUT.PUT_LINE('Reintento identico: retorna '||v_cantidad||', sin insertar otra fila.');
    BEGIN
        pkg_clases.confirmar_clase(v_clase,LOWER(RAWTOHEX(SYS_GUID())),'VOZ',v_carga,v_cantidad);
        RAISE_APPLICATION_ERROR(-20090,'Se admitio una segunda propuesta.');
    EXCEPTION WHEN OTHERS THEN
        IF SQLCODE<>-20074 THEN RAISE; END IF;
        DBMS_OUTPUT.PUT_LINE('Segunda propuesta rechazada: clase ya confirmada.');
    END;
    FOR r IN (SELECT clase_id,presente_detectado,presente,corregido_manual,motivo_correccion,revisado_por
              FROM registros_asistencia WHERE clase_id=v_clase) LOOP
        DBMS_OUTPUT.PUT_LINE('Clase='||r.clase_id||' deteccion='||r.presente_detectado||' final='||r.presente||
            ' correccion='||r.corregido_manual||' revisor='||r.revisado_por||' motivo='||r.motivo_correccion);
    END LOOP;
    ROLLBACK TO laboratorio_clases;
    pkg_auditoria.limpiar_contexto;
    DBMS_OUTPUT.PUT_LINE('Rollback final: no quedan fixtures del laboratorio.');
EXCEPTION WHEN OTHERS THEN
    ROLLBACK TO laboratorio_clases;
    pkg_auditoria.limpiar_contexto;
    RAISE;
END;
/
