--------------------------------------------------------------------------------
-- ControlDeAsistencia - Script Oracle XE 18c (usuario: oscar)
--------------------------------------------------------------------------------
-- Ejecutar TODO este script de una sola vez en SQL Developer, conectado
-- con una conexion SYSTEM o "SYS AS SYSDBA" contra el PDB XEPDB1.
-- Ejecutar como Script (boton "Run Script" o tecla F5), NO como sentencia unica.
-- Tambien desde consola:  sqlplus system@localhost:1521/XEPDB1 @oracle_scripts.sql
--
-- Crea en un solo paso:
--   * oscar   -> dueno de las tablas; lo usa la aplicacion.
--   * auditor -> usuario de SOLO LECTURA para el profesor/auditor.
--   * Tablas de la app + tabla AUDITORIA con triggers que registran
--     cada INSERT/UPDATE/DELETE (quien, cuando, desde donde, antes/despues).
--
-- ATENCION: borra y recrea los usuarios oscar y auditor (se pierden sus datos).
-- Cierra la aplicacion antes de ejecutarlo (ORA-01940 si hay sesiones abiertas).
--------------------------------------------------------------------------------

-- Elimina los usuarios si ya existian de una ejecucion previa (evita conflictos)
BEGIN
    EXECUTE IMMEDIATE 'DROP USER auditor CASCADE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -1918 THEN -- ORA-01918: user does not exist
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP USER oscar CASCADE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -1918 THEN -- ORA-01918: user does not exist
            RAISE;
        END IF;
END;
/

CREATE USER oscar IDENTIFIED BY "Contrasena.123"; -- (contraseña estándar: cámbiala por la tuya)

GRANT CONNECT, RESOURCE TO oscar;
GRANT CREATE SESSION TO oscar;
GRANT CREATE TABLE TO oscar;
GRANT CREATE SEQUENCE TO oscar;
GRANT CREATE VIEW TO oscar;
GRANT CREATE TRIGGER TO oscar;
GRANT UNLIMITED TABLESPACE TO oscar;

-- Usuario del profesor/auditor: solo puede conectarse y consultar (SELECT).
CREATE USER auditor IDENTIFIED BY "Auditor.123"; -- (contraseña estándar: cámbiala por la tuya)
GRANT CREATE SESSION TO auditor;

COMMIT;

-- A partir de aqui, todo lo que se cree quedara dentro del esquema de "oscar",
-- aunque sigamos conectados como SYSTEM/SYSDBA.
ALTER SESSION SET CURRENT_SCHEMA = oscar;

-- ============================================================
-- Eliminacion segura de objetos previos (respeta dependencias)
-- ============================================================
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE registros_asistencia CASCADE CONSTRAINTS PURGE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN -- ORA-00942: table or view does not exist
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE materia_estudiantes CASCADE CONSTRAINTS PURGE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE materias CASCADE CONSTRAINTS PURGE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE estudiantes CASCADE CONSTRAINTS PURGE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE profesores CASCADE CONSTRAINTS PURGE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN
            RAISE;
        END IF;
END;
/

-- ============================================================
-- PROFESORES
-- ============================================================
CREATE TABLE profesores (
    profesor_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario       VARCHAR2(100)  NOT NULL,
    contrasena    VARCHAR2(255)  NOT NULL,
    nombre        VARCHAR2(200)  NOT NULL,
    creado_en     TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT uq_profesores_usuario UNIQUE (usuario)
);

-- ============================================================
-- ESTUDIANTES
-- ============================================================
CREATE TABLE estudiantes (
    estudiante_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre            VARCHAR2(200) NOT NULL,
    embedding_facial  CLOB,
    embedding_voz     CLOB,
    creado_en         TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT ck_estudiantes_facial_json CHECK (embedding_facial IS JSON),
    CONSTRAINT ck_estudiantes_voz_json    CHECK (embedding_voz    IS JSON)
);

-- ============================================================
-- MATERIAS
-- ============================================================
CREATE TABLE materias (
    materia_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_materia   VARCHAR2(50)  NOT NULL,
    nombre           VARCHAR2(200) NOT NULL,
    seccion          VARCHAR2(100),
    profesor_id      NUMBER NOT NULL,
    creado_en        TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT uq_materias_codigo UNIQUE (codigo_materia),
    CONSTRAINT fk_materias_profesor FOREIGN KEY (profesor_id)
        REFERENCES profesores (profesor_id) ON DELETE CASCADE
);

CREATE INDEX ix_materias_profesor ON materias (profesor_id);

-- ============================================================
-- MATERIA_ESTUDIANTES (matriculas)
-- ============================================================
CREATE TABLE materia_estudiantes (
    materia_id      NUMBER NOT NULL,
    estudiante_id   NUMBER NOT NULL,
    matriculado_en  TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT pk_materia_estudiantes PRIMARY KEY (materia_id, estudiante_id),
    CONSTRAINT fk_me_materia FOREIGN KEY (materia_id)
        REFERENCES materias (materia_id) ON DELETE CASCADE,
    CONSTRAINT fk_me_estudiante FOREIGN KEY (estudiante_id)
        REFERENCES estudiantes (estudiante_id) ON DELETE CASCADE
);

CREATE INDEX ix_me_estudiante ON materia_estudiantes (estudiante_id);

-- ============================================================
-- REGISTROS_ASISTENCIA
-- ============================================================
CREATE TABLE registros_asistencia (
    asistencia_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    materia_id        NUMBER NOT NULL,
    estudiante_id     NUMBER NOT NULL,
    fecha_hora        TIMESTAMP WITH TIME ZONE NOT NULL,
    presente          NUMBER(1) DEFAULT 0 NOT NULL,
    CONSTRAINT ck_asistencia_presente CHECK (presente IN (0,1)),
    CONSTRAINT fk_ra_materia FOREIGN KEY (materia_id)
        REFERENCES materias (materia_id) ON DELETE CASCADE,
    CONSTRAINT fk_ra_estudiante FOREIGN KEY (estudiante_id)
        REFERENCES estudiantes (estudiante_id) ON DELETE CASCADE
);

CREATE INDEX ix_ra_materia    ON registros_asistencia (materia_id);
CREATE INDEX ix_ra_estudiante ON registros_asistencia (estudiante_id);
CREATE INDEX ix_ra_fecha      ON registros_asistencia (fecha_hora);

-- ============================================================
-- AUDITORIA (registro de cambios)
-- ============================================================
-- usuario_app lo envia la aplicacion en cada conexion (CLIENT_IDENTIFIER),
-- p. ej. "profesor:jperez" o "estudiante:5:Ana Diaz". Si el cambio se hace
-- directo en SQL Developer queda vacio y se ve el usuario_bd / usuario_so.
-- Los embeddings y la contrasena NO se copian aqui (solo si existen / ***).
CREATE TABLE auditoria (
    auditoria_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha          TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
    tabla          VARCHAR2(30)  NOT NULL,
    operacion      VARCHAR2(6)   NOT NULL,
    registro_id    VARCHAR2(100),
    usuario_app    VARCHAR2(256) DEFAULT SYS_CONTEXT('USERENV', 'CLIENT_IDENTIFIER'),
    usuario_bd     VARCHAR2(256) DEFAULT SYS_CONTEXT('USERENV', 'SESSION_USER'),
    usuario_so     VARCHAR2(256) DEFAULT SYS_CONTEXT('USERENV', 'OS_USER'),
    programa       VARCHAR2(256) DEFAULT SYS_CONTEXT('USERENV', 'MODULE'),
    equipo         VARCHAR2(256) DEFAULT SYS_CONTEXT('USERENV', 'HOST'),
    ip             VARCHAR2(256) DEFAULT SYS_CONTEXT('USERENV', 'IP_ADDRESS'),
    datos_antes    VARCHAR2(4000),
    datos_despues  VARCHAR2(4000),
    CONSTRAINT ck_aud_operacion CHECK (operacion IN ('INSERT', 'UPDATE', 'DELETE')),
    CONSTRAINT ck_aud_antes_json   CHECK (datos_antes   IS JSON),
    CONSTRAINT ck_aud_despues_json CHECK (datos_despues IS JSON)
);

CREATE INDEX ix_aud_fecha ON auditoria (fecha);
CREATE INDEX ix_aud_tabla ON auditoria (tabla, registro_id);

-- La auditoria no se puede alterar: bloquea UPDATE y DELETE sobre ella.
CREATE OR REPLACE TRIGGER trg_auditoria_inmutable
BEFORE UPDATE OR DELETE ON auditoria
FOR EACH ROW
BEGIN
    RAISE_APPLICATION_ERROR(-20001, 'Los registros de auditoria no se pueden modificar ni borrar.');
END;
/

CREATE OR REPLACE TRIGGER trg_aud_profesores
AFTER INSERT OR UPDATE OR DELETE ON profesores
FOR EACH ROW
DECLARE
    v_op      VARCHAR2(6);
    v_antes   VARCHAR2(4000);
    v_despues VARCHAR2(4000);
BEGIN
    v_op := CASE WHEN INSERTING THEN 'INSERT' WHEN UPDATING THEN 'UPDATE' ELSE 'DELETE' END;
    IF NOT INSERTING THEN
        SELECT JSON_OBJECT('profesor_id' VALUE :OLD.profesor_id, 'usuario' VALUE :OLD.usuario,
                           'nombre' VALUE :OLD.nombre, 'contrasena' VALUE '***')
          INTO v_antes FROM dual;
    END IF;
    IF NOT DELETING THEN
        SELECT JSON_OBJECT('profesor_id' VALUE :NEW.profesor_id, 'usuario' VALUE :NEW.usuario,
                           'nombre' VALUE :NEW.nombre, 'contrasena' VALUE '***')
          INTO v_despues FROM dual;
    END IF;
    INSERT INTO auditoria (tabla, operacion, registro_id, datos_antes, datos_despues)
    VALUES ('PROFESORES', v_op, TO_CHAR(NVL(:NEW.profesor_id, :OLD.profesor_id)), v_antes, v_despues);
END;
/

CREATE OR REPLACE TRIGGER trg_aud_estudiantes
AFTER INSERT OR UPDATE OR DELETE ON estudiantes
FOR EACH ROW
DECLARE
    v_op      VARCHAR2(6);
    v_antes   VARCHAR2(4000);
    v_despues VARCHAR2(4000);
BEGIN
    v_op := CASE WHEN INSERTING THEN 'INSERT' WHEN UPDATING THEN 'UPDATE' ELSE 'DELETE' END;
    IF NOT INSERTING THEN
        SELECT JSON_OBJECT('estudiante_id' VALUE :OLD.estudiante_id, 'nombre' VALUE :OLD.nombre,
                           'tiene_rostro' VALUE CASE WHEN :OLD.embedding_facial IS NULL THEN 'no' ELSE 'si' END,
                           'tiene_voz'    VALUE CASE WHEN :OLD.embedding_voz    IS NULL THEN 'no' ELSE 'si' END)
          INTO v_antes FROM dual;
    END IF;
    IF NOT DELETING THEN
        SELECT JSON_OBJECT('estudiante_id' VALUE :NEW.estudiante_id, 'nombre' VALUE :NEW.nombre,
                           'tiene_rostro' VALUE CASE WHEN :NEW.embedding_facial IS NULL THEN 'no' ELSE 'si' END,
                           'tiene_voz'    VALUE CASE WHEN :NEW.embedding_voz    IS NULL THEN 'no' ELSE 'si' END)
          INTO v_despues FROM dual;
    END IF;
    INSERT INTO auditoria (tabla, operacion, registro_id, datos_antes, datos_despues)
    VALUES ('ESTUDIANTES', v_op, TO_CHAR(NVL(:NEW.estudiante_id, :OLD.estudiante_id)), v_antes, v_despues);
END;
/

CREATE OR REPLACE TRIGGER trg_aud_materias
AFTER INSERT OR UPDATE OR DELETE ON materias
FOR EACH ROW
DECLARE
    v_op      VARCHAR2(6);
    v_antes   VARCHAR2(4000);
    v_despues VARCHAR2(4000);
BEGIN
    v_op := CASE WHEN INSERTING THEN 'INSERT' WHEN UPDATING THEN 'UPDATE' ELSE 'DELETE' END;
    IF NOT INSERTING THEN
        SELECT JSON_OBJECT('materia_id' VALUE :OLD.materia_id, 'codigo_materia' VALUE :OLD.codigo_materia,
                           'nombre' VALUE :OLD.nombre, 'seccion' VALUE :OLD.seccion,
                           'profesor_id' VALUE :OLD.profesor_id)
          INTO v_antes FROM dual;
    END IF;
    IF NOT DELETING THEN
        SELECT JSON_OBJECT('materia_id' VALUE :NEW.materia_id, 'codigo_materia' VALUE :NEW.codigo_materia,
                           'nombre' VALUE :NEW.nombre, 'seccion' VALUE :NEW.seccion,
                           'profesor_id' VALUE :NEW.profesor_id)
          INTO v_despues FROM dual;
    END IF;
    INSERT INTO auditoria (tabla, operacion, registro_id, datos_antes, datos_despues)
    VALUES ('MATERIAS', v_op, TO_CHAR(NVL(:NEW.materia_id, :OLD.materia_id)), v_antes, v_despues);
END;
/

CREATE OR REPLACE TRIGGER trg_aud_materia_estudiantes
AFTER INSERT OR UPDATE OR DELETE ON materia_estudiantes
FOR EACH ROW
DECLARE
    v_op      VARCHAR2(6);
    v_antes   VARCHAR2(4000);
    v_despues VARCHAR2(4000);
BEGIN
    v_op := CASE WHEN INSERTING THEN 'INSERT' WHEN UPDATING THEN 'UPDATE' ELSE 'DELETE' END;
    IF NOT INSERTING THEN
        SELECT JSON_OBJECT('materia_id' VALUE :OLD.materia_id, 'estudiante_id' VALUE :OLD.estudiante_id)
          INTO v_antes FROM dual;
    END IF;
    IF NOT DELETING THEN
        SELECT JSON_OBJECT('materia_id' VALUE :NEW.materia_id, 'estudiante_id' VALUE :NEW.estudiante_id)
          INTO v_despues FROM dual;
    END IF;
    INSERT INTO auditoria (tabla, operacion, registro_id, datos_antes, datos_despues)
    VALUES ('MATERIA_ESTUDIANTES', v_op,
            NVL(:NEW.materia_id, :OLD.materia_id) || '-' || NVL(:NEW.estudiante_id, :OLD.estudiante_id),
            v_antes, v_despues);
END;
/

CREATE OR REPLACE TRIGGER trg_aud_registros_asistencia
AFTER INSERT OR UPDATE OR DELETE ON registros_asistencia
FOR EACH ROW
DECLARE
    v_op      VARCHAR2(6);
    v_antes   VARCHAR2(4000);
    v_despues VARCHAR2(4000);
BEGIN
    v_op := CASE WHEN INSERTING THEN 'INSERT' WHEN UPDATING THEN 'UPDATE' ELSE 'DELETE' END;
    IF NOT INSERTING THEN
        SELECT JSON_OBJECT('asistencia_id' VALUE :OLD.asistencia_id, 'materia_id' VALUE :OLD.materia_id,
                           'estudiante_id' VALUE :OLD.estudiante_id,
                           'fecha_hora' VALUE TO_CHAR(:OLD.fecha_hora, 'YYYY-MM-DD HH24:MI:SS TZH:TZM'),
                           'presente' VALUE :OLD.presente)
          INTO v_antes FROM dual;
    END IF;
    IF NOT DELETING THEN
        SELECT JSON_OBJECT('asistencia_id' VALUE :NEW.asistencia_id, 'materia_id' VALUE :NEW.materia_id,
                           'estudiante_id' VALUE :NEW.estudiante_id,
                           'fecha_hora' VALUE TO_CHAR(:NEW.fecha_hora, 'YYYY-MM-DD HH24:MI:SS TZH:TZM'),
                           'presente' VALUE :NEW.presente)
          INTO v_despues FROM dual;
    END IF;
    INSERT INTO auditoria (tabla, operacion, registro_id, datos_antes, datos_despues)
    VALUES ('REGISTROS_ASISTENCIA', v_op, TO_CHAR(NVL(:NEW.asistencia_id, :OLD.asistencia_id)), v_antes, v_despues);
END;
/

-- ============================================================
-- VISTA para el auditor: asistencia con nombres en vez de IDs
-- ============================================================
CREATE OR REPLACE VIEW vista_asistencia_detallada AS
SELECT ra.asistencia_id,
       ra.fecha_hora,
       m.codigo_materia,
       m.nombre        AS materia,
       m.seccion,
       p.nombre        AS profesor,
       e.estudiante_id,
       e.nombre        AS estudiante,
       CASE ra.presente WHEN 1 THEN 'Presente' ELSE 'Ausente' END AS estado
FROM registros_asistencia ra
JOIN materias    m ON m.materia_id    = ra.materia_id
JOIN profesores  p ON p.profesor_id   = m.profesor_id
JOIN estudiantes e ON e.estudiante_id = ra.estudiante_id;

-- ============================================================
-- PERMISOS DE SOLO LECTURA para el auditor
-- (la contrasena de profesores y los embeddings se ven, pero son hash/vectores)
-- ============================================================
GRANT SELECT ON profesores                 TO auditor;
GRANT SELECT ON estudiantes                TO auditor;
GRANT SELECT ON materias                   TO auditor;
GRANT SELECT ON materia_estudiantes        TO auditor;
GRANT SELECT ON registros_asistencia       TO auditor;
GRANT SELECT ON auditoria                  TO auditor;
GRANT SELECT ON vista_asistencia_detallada TO auditor;

COMMIT;

-- Verificacion rapida: deben salir 6 tablas y 6 triggers ENABLED;
-- la ultima consulta (objetos invalidos) NO debe devolver filas.
SELECT table_name FROM all_tables WHERE owner = 'OSCAR' ORDER BY table_name;
SELECT trigger_name, status FROM all_triggers WHERE owner = 'OSCAR' ORDER BY trigger_name;
SELECT object_name, object_type, status FROM all_objects
 WHERE owner = 'OSCAR' AND object_type IN ('TRIGGER', 'VIEW') AND status <> 'VALID';

--------------------------------------------------------------------------------
-- Conexion de la aplicacion (Python / Streamlit) - ya configurada por defecto:
--     ORACLE_USUARIO    = oscar
--     ORACLE_CONTRASENA = Contrasena.123   (contraseña estándar: cámbiala por la tuya)
--     ORACLE_DSN        = localhost:1521/XEPDB1
--
-- Conexion del profesor/auditor (SQL Developer, solo lectura):
--     Usuario: auditor   Contrasena: Auditor.123   (contraseña estándar: cámbiala por la tuya)
--     Servicio: XEPDB1   Puerto: 1521
--     Ejemplos:
--       SELECT * FROM oscar.auditoria ORDER BY fecha DESC;
--       SELECT * FROM oscar.vista_asistencia_detallada ORDER BY fecha_hora DESC;
--------------------------------------------------------------------------------
