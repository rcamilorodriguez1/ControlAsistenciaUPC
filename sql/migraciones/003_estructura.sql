-- Ejecutar con la aplicacion detenida y un respaldo previo. DDL hace COMMIT implicito.
-- Recuperable tras un fallo parcial; nunca elimina registros historicos.
DECLARE
    v_n NUMBER;
    PROCEDURE columna(p_tabla VARCHAR2, p_nombre VARCHAR2, p_def VARCHAR2) IS
    BEGIN
        SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name=p_tabla AND column_name=p_nombre;
        IF v_n=0 THEN EXECUTE IMMEDIATE 'ALTER TABLE '||p_tabla||' ADD ('||p_def||')'; END IF;
    END;
BEGIN
    IF SYS_CONTEXT('USERENV','SESSION_USER') IN ('SYS','SYSTEM') OR SYS_CONTEXT('USERENV','CON_NAME')='CDB$ROOT' THEN
        RAISE_APPLICATION_ERROR(-20070,'Ejecute 003 como usuario de la aplicacion en el PDB.');
    END IF;
    SELECT COUNT(*) INTO v_n FROM versiones_esquema WHERE version='002';
    IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20070,'Se requiere la migracion 002.'); END IF;
    SELECT COUNT(*) INTO v_n FROM versiones_esquema WHERE version='003';
    IF v_n=1 THEN RETURN; END IF;
    SELECT COUNT(*) INTO v_n FROM user_tables WHERE table_name='CLASES';
    IF v_n=0 THEN
        EXECUTE IMMEDIATE q'~CREATE TABLE clases (
            clase_id NUMBER GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_clases PRIMARY KEY,
            materia_id NUMBER NOT NULL,
            profesor_id NUMBER NOT NULL,
            fecha_hora TIMESTAMP WITH TIME ZONE NOT NULL,
            instante_utc GENERATED ALWAYS AS (SYS_EXTRACT_UTC(fecha_hora)) VIRTUAL,
            lote_legado NUMBER DEFAULT 0 NOT NULL,
            estado VARCHAR2(12 CHAR) DEFAULT 'BORRADOR' NOT NULL,
            origen VARCHAR2(12 CHAR) DEFAULT 'PENDIENTE' NOT NULL,
            clave_confirmacion VARCHAR2(32 CHAR),
            propuesta_confirmada CLOB,
            registros_confirmados NUMBER DEFAULT 0 NOT NULL,
            creado_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
            confirmado_en TIMESTAMP WITH TIME ZONE,
            CONSTRAINT fk_clases_materia FOREIGN KEY (materia_id) REFERENCES materias(materia_id) ON DELETE CASCADE,
            CONSTRAINT uq_clases_instante UNIQUE (materia_id,instante_utc,lote_legado),
            CONSTRAINT uq_clases_materia UNIQUE (clase_id,materia_id),
            CONSTRAINT uq_clases_confirmacion UNIQUE (clave_confirmacion),
            CONSTRAINT ck_clases_estado CHECK (estado IN ('BORRADOR','CONFIRMADA')),
            CONSTRAINT ck_clases_origen CHECK (origen IN ('PENDIENTE','FACIAL','VOZ','LEGADO')),
            CONSTRAINT ck_clases_lote CHECK (lote_legado>=0 AND lote_legado=TRUNC(lote_legado) AND (lote_legado=0 OR origen='LEGADO')),
            CONSTRAINT ck_clases_json CHECK (propuesta_confirmada IS JSON),
            CONSTRAINT ck_clases_cantidad CHECK (registros_confirmados>=0 AND registros_confirmados=TRUNC(registros_confirmados)),
            CONSTRAINT ck_clases_confirmada CHECK (
                (estado='BORRADOR' AND origen='PENDIENTE' AND clave_confirmacion IS NULL AND propuesta_confirmada IS NULL AND confirmado_en IS NULL)
                OR (estado='CONFIRMADA' AND origen='LEGADO' AND clave_confirmacion IS NULL AND confirmado_en IS NOT NULL)
                OR (estado='CONFIRMADA' AND origen IN ('FACIAL','VOZ') AND LENGTH(clave_confirmacion)=32 AND clave_confirmacion IS NOT NULL AND propuesta_confirmada IS NOT NULL AND confirmado_en IS NOT NULL))
        )~';
    END IF;
    columna('REGISTROS_ASISTENCIA','CLASE_ID','clase_id NUMBER');
    columna('REGISTROS_ASISTENCIA','PRESENTE_DETECTADO','presente_detectado NUMBER(1)');
    columna('REGISTROS_ASISTENCIA','CORREGIDO_MANUAL','corregido_manual NUMBER(1) DEFAULT 0 NOT NULL');
    columna('REGISTROS_ASISTENCIA','MOTIVO_CORRECCION','motivo_correccion VARCHAR2(500 CHAR)');
    columna('REGISTROS_ASISTENCIA','REVISADO_POR','revisado_por NUMBER');
    columna('REGISTROS_ASISTENCIA','REVISADO_EN','revisado_en TIMESTAMP WITH TIME ZONE');
    columna('AUDITORIA_ASISTENCIA','CLASE_ANTERIOR','clase_anterior NUMBER');
    columna('AUDITORIA_ASISTENCIA','CLASE_NUEVA','clase_nueva NUMBER');
    columna('AUDITORIA_ASISTENCIA','DETECTADO_ANTERIOR','detectado_anterior NUMBER(1)');
    columna('AUDITORIA_ASISTENCIA','CORRECCION_INICIAL','correccion_inicial NUMBER(1)');
    columna('AUDITORIA_ASISTENCIA','MOTIVO_INICIAL','motivo_inicial VARCHAR2(500 CHAR)');
    columna('AUDITORIA_ASISTENCIA','REVISOR_INICIAL','revisor_inicial NUMBER');
END;
/
-- Compilar este bloque solo despues de que el DDL anterior haya creado sus tablas/columnas.
DECLARE
    v_n NUMBER;
    PROCEDURE restriccion(p_nombre VARCHAR2,p_ddl VARCHAR2) IS
    BEGIN
        SELECT COUNT(*) INTO v_n FROM user_constraints WHERE constraint_name=p_nombre;
        IF v_n=0 THEN EXECUTE IMMEDIATE p_ddl; END IF;
    END;
BEGIN
    SELECT COUNT(*) INTO v_n FROM versiones_esquema WHERE version='003';
    IF v_n=1 THEN RETURN; END IF;
    -- La ocurrencia de cada estudiante desdobla duplicados del mismo instante sin borrarlos.
    MERGE INTO clases c USING (
        SELECT r.materia_id,m.profesor_id,r.utc,r.lote,MIN(r.fecha_hora) fecha_hora
        FROM (
            SELECT materia_id,fecha_hora,SYS_EXTRACT_UTC(fecha_hora) utc,
                   ROW_NUMBER() OVER (PARTITION BY materia_id,SYS_EXTRACT_UTC(fecha_hora),estudiante_id ORDER BY asistencia_id)-1 lote
            FROM registros_asistencia
        ) r JOIN materias m ON m.materia_id=r.materia_id
        GROUP BY r.materia_id,m.profesor_id,r.utc,r.lote
    ) h ON (c.materia_id=h.materia_id AND c.instante_utc=h.utc AND c.lote_legado=h.lote)
    WHEN NOT MATCHED THEN INSERT(materia_id,profesor_id,fecha_hora,lote_legado,estado,origen,confirmado_en)
        VALUES(h.materia_id,h.profesor_id,h.fecha_hora,h.lote,'CONFIRMADA','LEGADO',SYSTIMESTAMP);

    MERGE INTO registros_asistencia ra USING (
        SELECT r.asistencia_id,c.clase_id FROM (
            SELECT asistencia_id,materia_id,SYS_EXTRACT_UTC(fecha_hora) utc,
                   ROW_NUMBER() OVER (PARTITION BY materia_id,SYS_EXTRACT_UTC(fecha_hora),estudiante_id ORDER BY asistencia_id)-1 lote
            FROM registros_asistencia
        ) r JOIN clases c ON c.materia_id=r.materia_id AND c.instante_utc=r.utc AND c.lote_legado=r.lote
    ) h ON (ra.asistencia_id=h.asistencia_id)
    WHEN MATCHED THEN UPDATE SET ra.clase_id=h.clase_id,ra.presente_detectado=ra.presente
        WHERE ra.clase_id IS NULL;
    UPDATE clases c SET registros_confirmados=(SELECT COUNT(*) FROM registros_asistencia ra WHERE ra.clase_id=c.clase_id)
        WHERE origen='LEGADO';
    COMMIT;
    -- No solicitar MODIFY NOT NULL de nuevo si se recupera un DDL parcial.
    SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='REGISTROS_ASISTENCIA' AND column_name='CLASE_ID' AND nullable='Y';
    IF v_n>0 THEN EXECUTE IMMEDIATE 'ALTER TABLE registros_asistencia MODIFY clase_id NOT NULL'; END IF;
    SELECT COUNT(*) INTO v_n FROM user_tab_columns WHERE table_name='REGISTROS_ASISTENCIA' AND column_name='PRESENTE_DETECTADO' AND nullable='Y';
    IF v_n>0 THEN EXECUTE IMMEDIATE 'ALTER TABLE registros_asistencia MODIFY presente_detectado NOT NULL'; END IF;
    restriccion('UQ_RA_CLASE_ESTUDIANTE','ALTER TABLE registros_asistencia ADD CONSTRAINT uq_ra_clase_estudiante UNIQUE(clase_id,estudiante_id)');
    restriccion('FK_RA_CLASE_MATERIA','ALTER TABLE registros_asistencia ADD CONSTRAINT fk_ra_clase_materia FOREIGN KEY(clase_id,materia_id) REFERENCES clases(clase_id,materia_id) ON DELETE CASCADE');
    restriccion('CK_RA_DETECTADO','ALTER TABLE registros_asistencia ADD CONSTRAINT ck_ra_detectado CHECK(presente_detectado IN (0,1))');
    restriccion('CK_RA_CORREGIDO','ALTER TABLE registros_asistencia ADD CONSTRAINT ck_ra_corregido CHECK(corregido_manual IN (0,1))');
    restriccion('CK_RA_REVISION',q'~ALTER TABLE registros_asistencia ADD CONSTRAINT ck_ra_revision CHECK (
        (corregido_manual=0 AND motivo_correccion IS NULL AND revisado_por IS NULL AND revisado_en IS NULL)
        OR (corregido_manual=1 AND TRIM(motivo_correccion) IS NOT NULL AND revisado_por IS NOT NULL AND revisado_en IS NOT NULL))~');
END;
/
COMMENT ON TABLE clases IS 'Clase identificada por materia e instante UTC; una confirmacion durable compartida por pestañas.';
COMMENT ON COLUMN clases.lote_legado IS '0 para clases nuevas; ocurrencias historicas duplicadas se conservan en lotes 1,2,...';
COMMENT ON COLUMN clases.profesor_id IS 'Responsable al crear la clase, conservado como instantanea.';
COMMENT ON COLUMN clases.propuesta_confirmada IS 'Carga canonica de la confirmacion para reconocer reintentos; sin biometria.';
COMMENT ON COLUMN registros_asistencia.fecha_hora IS 'Instante del analisis; el horario de clase esta en CLASES.FECHA_HORA.';
COMMENT ON COLUMN registros_asistencia.corregido_manual IS 'Correccion previa a la primera confirmacion; las ediciones posteriores se auditan con el disparador.';
