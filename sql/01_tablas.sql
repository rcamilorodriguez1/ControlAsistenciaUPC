-- Instalacion inicial 001. Requiere un esquema NUEVO y vacio.
-- DDL Oracle hace COMMIT implicito: no reejecutar como una migracion.
DECLARE
    v_objetos NUMBER;
BEGIN
    IF SYS_CONTEXT('USERENV', 'CURRENT_USER') IN ('SYS', 'SYSTEM')
       OR SYS_CONTEXT('USERENV', 'CON_NAME') = 'CDB$ROOT' THEN
        RAISE_APPLICATION_ERROR(-20004, 'Conectese como usuario de la aplicacion al PDB.');
    END IF;
    SELECT COUNT(*) INTO v_objetos FROM user_objects;
    IF v_objetos > 0 THEN
        RAISE_APPLICATION_ERROR(-20005, 'El esquema no esta vacio. Use migraciones; no se eliminaron objetos.');
    END IF;
END;
/

CREATE TABLE versiones_esquema (
    version VARCHAR2(20) CONSTRAINT pk_versiones_esquema PRIMARY KEY,
    descripcion VARCHAR2(200) NOT NULL,
    aplicado_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL
);
CREATE TABLE profesores (
    profesor_id NUMBER GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_profesores PRIMARY KEY,
    usuario VARCHAR2(100 CHAR) NOT NULL,
    contrasena VARCHAR2(255 CHAR) NOT NULL,
    nombre VARCHAR2(200 CHAR) NOT NULL,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT uq_profesores_usuario UNIQUE (usuario)
);
CREATE TABLE estudiantes (
    estudiante_id NUMBER GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_estudiantes PRIMARY KEY,
    nombre VARCHAR2(200 CHAR) NOT NULL,
    embedding_facial CLOB,
    embedding_voz CLOB,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT ck_estudiantes_facial_json CHECK (embedding_facial IS JSON),
    CONSTRAINT ck_estudiantes_voz_json CHECK (embedding_voz IS JSON)
);
CREATE TABLE materias (
    materia_id NUMBER GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_materias PRIMARY KEY,
    codigo_materia VARCHAR2(50 CHAR) NOT NULL,
    nombre VARCHAR2(200 CHAR) NOT NULL,
    seccion VARCHAR2(100 CHAR),
    profesor_id NUMBER NOT NULL,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT uq_materias_codigo UNIQUE (codigo_materia),
    CONSTRAINT fk_materias_profesor FOREIGN KEY (profesor_id)
        REFERENCES profesores (profesor_id) ON DELETE CASCADE
);
CREATE INDEX ix_materias_profesor ON materias (profesor_id);
CREATE TABLE materia_estudiantes (
    materia_id NUMBER NOT NULL,
    estudiante_id NUMBER NOT NULL,
    matriculado_en TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT pk_materia_estudiantes PRIMARY KEY (materia_id, estudiante_id),
    CONSTRAINT fk_me_materia FOREIGN KEY (materia_id)
        REFERENCES materias (materia_id) ON DELETE CASCADE,
    CONSTRAINT fk_me_estudiante FOREIGN KEY (estudiante_id)
        REFERENCES estudiantes (estudiante_id) ON DELETE CASCADE
);
CREATE INDEX ix_me_estudiante ON materia_estudiantes (estudiante_id);
CREATE TABLE registros_asistencia (
    asistencia_id NUMBER GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_registros_asistencia PRIMARY KEY,
    materia_id NUMBER NOT NULL,
    estudiante_id NUMBER NOT NULL,
    fecha_hora TIMESTAMP WITH TIME ZONE NOT NULL,
    presente NUMBER(1) DEFAULT 0 NOT NULL,
    CONSTRAINT ck_asistencia_presente CHECK (presente IN (0, 1)),
    CONSTRAINT fk_ra_materia FOREIGN KEY (materia_id)
        REFERENCES materias (materia_id) ON DELETE CASCADE,
    CONSTRAINT fk_ra_estudiante FOREIGN KEY (estudiante_id)
        REFERENCES estudiantes (estudiante_id) ON DELETE CASCADE
);
CREATE INDEX ix_ra_materia ON registros_asistencia (materia_id);
CREATE INDEX ix_ra_estudiante ON registros_asistencia (estudiante_id);
CREATE INDEX ix_ra_fecha ON registros_asistencia (fecha_hora);

COMMENT ON TABLE profesores IS 'Cuentas docentes; la contrasena contiene un hash bcrypt.';
COMMENT ON TABLE estudiantes IS 'Perfiles estudiantiles y vectores biometricos JSON; no guarda fotos ni audio.';
COMMENT ON TABLE materias IS 'Materias y secciones administradas por un profesor.';
COMMENT ON TABLE materia_estudiantes IS 'Relacion muchos a muchos entre estudiantes y materias.';
COMMENT ON TABLE registros_asistencia IS 'Resultados individuales de las tomas de asistencia.';
COMMENT ON TABLE versiones_esquema IS 'Versiones de instalacion y futuras migraciones aplicadas.';
COMMENT ON COLUMN registros_asistencia.fecha_hora IS 'Instante con zona horaria; la aplicacion presenta America/Bogota.';
COMMENT ON COLUMN estudiantes.embedding_facial IS 'Vector facial de 128 dimensiones serializado como JSON.';
COMMENT ON COLUMN estudiantes.embedding_voz IS 'Vector de hablante de 256 dimensiones serializado como JSON, opcional.';
-- La version se registra al terminar TODA la instalacion y su verificacion,
-- desde 07_registrar_version.sql. El DDL anterior tiene commits implicitos.
