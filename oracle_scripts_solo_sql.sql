--------------------------------------------------------------------------------
-- Control De Asistencia UPC - Script Oracle XE 18c/21c (SOLO SQL, sin PL/SQL)
-- Usuario de la aplicacion: Asistencia_UPC
--------------------------------------------------------------------------------
-- Ejecutar conectado como SYSTEM al servicio XEPDB1:
--   * SQL Developer: abrir este archivo y pulsar F5 (Run Script).
--   * Consola:       sqlplus system@localhost:1521/XEPDB1 "@oracle_scripts_solo_sql.sql"
-- La PRIMERA vez, los NOAUDIT/DROP del inicio daran error (ORA-46357,
-- ORA-01918) porque no hay nada que borrar: es normal, el script continua.
-- ATENCION: borra y recrea los usuarios Asistencia_UPC y auditor.
--------------------------------------------------------------------------------

-- ============================================================
-- LIMPIEZA DE EJECUCIONES ANTERIORES
-- ============================================================
NOAUDIT POLICY pol_auditoria_asistencia;
DROP AUDIT POLICY pol_auditoria_asistencia;
DROP USER auditor CASCADE;
DROP USER Asistencia_UPC CASCADE;

-- ============================================================
-- USUARIOS
-- ============================================================
CREATE USER Asistencia_UPC IDENTIFIED BY "UPC123"; -- (contraseña estándar: cámbiala por la tuya)

GRANT CONNECT, RESOURCE TO Asistencia_UPC;
GRANT CREATE SESSION TO Asistencia_UPC;
GRANT CREATE TABLE TO Asistencia_UPC;
GRANT CREATE SEQUENCE TO Asistencia_UPC;
GRANT CREATE VIEW TO Asistencia_UPC;
GRANT UNLIMITED TABLESPACE TO Asistencia_UPC;

-- Profesor/auditor: solo puede conectarse, consultar y leer la auditoria.
CREATE USER auditor IDENTIFIED BY "Auditor.123"; -- (contraseña estándar: cámbiala por la tuya)
GRANT CREATE SESSION TO auditor;
GRANT AUDIT_VIEWER TO auditor;

-- ============================================================
-- PROFESORES
-- ============================================================
CREATE TABLE Asistencia_UPC.profesores (
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
CREATE TABLE Asistencia_UPC.estudiantes (
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
CREATE TABLE Asistencia_UPC.materias (
    materia_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_materia   VARCHAR2(50)  NOT NULL,
    nombre           VARCHAR2(200) NOT NULL,
    seccion          VARCHAR2(100),
    profesor_id      NUMBER NOT NULL,
    creado_en        TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT uq_materias_codigo UNIQUE (codigo_materia),
    CONSTRAINT fk_materias_profesor FOREIGN KEY (profesor_id)
        REFERENCES Asistencia_UPC.profesores (profesor_id) ON DELETE CASCADE
);

CREATE INDEX Asistencia_UPC.ix_materias_profesor ON Asistencia_UPC.materias (profesor_id);

-- ============================================================
-- MATERIA_ESTUDIANTES (matriculas)
-- ============================================================
CREATE TABLE Asistencia_UPC.materia_estudiantes (
    materia_id      NUMBER NOT NULL,
    estudiante_id   NUMBER NOT NULL,
    matriculado_en  TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT pk_materia_estudiantes PRIMARY KEY (materia_id, estudiante_id),
    CONSTRAINT fk_me_materia FOREIGN KEY (materia_id)
        REFERENCES Asistencia_UPC.materias (materia_id) ON DELETE CASCADE,
    CONSTRAINT fk_me_estudiante FOREIGN KEY (estudiante_id)
        REFERENCES Asistencia_UPC.estudiantes (estudiante_id) ON DELETE CASCADE
);

CREATE INDEX Asistencia_UPC.ix_me_estudiante ON Asistencia_UPC.materia_estudiantes (estudiante_id);

-- ============================================================
-- REGISTROS_ASISTENCIA
-- ============================================================
CREATE TABLE Asistencia_UPC.registros_asistencia (
    asistencia_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    materia_id        NUMBER NOT NULL,
    estudiante_id     NUMBER NOT NULL,
    fecha_hora        TIMESTAMP WITH TIME ZONE NOT NULL,
    presente          NUMBER(1) DEFAULT 0 NOT NULL,
    CONSTRAINT ck_asistencia_presente CHECK (presente IN (0, 1)),
    CONSTRAINT fk_ra_materia FOREIGN KEY (materia_id)
        REFERENCES Asistencia_UPC.materias (materia_id) ON DELETE CASCADE,
    CONSTRAINT fk_ra_estudiante FOREIGN KEY (estudiante_id)
        REFERENCES Asistencia_UPC.estudiantes (estudiante_id) ON DELETE CASCADE
);

CREATE INDEX Asistencia_UPC.ix_ra_materia ON Asistencia_UPC.registros_asistencia (materia_id);
CREATE INDEX Asistencia_UPC.ix_ra_estudiante ON Asistencia_UPC.registros_asistencia (estudiante_id);
CREATE INDEX Asistencia_UPC.ix_ra_fecha ON Asistencia_UPC.registros_asistencia (fecha_hora);

-- ============================================================
-- VISTA para el auditor: asistencia con nombres en vez de IDs
-- ============================================================
CREATE OR REPLACE VIEW Asistencia_UPC.vista_asistencia_detallada AS
SELECT ra.asistencia_id, ra.fecha_hora, m.codigo_materia, m.nombre materia, m.seccion,
p.nombre profesor, e.estudiante_id, e.nombre estudiante,
CASE WHEN ra.presente = 1 THEN 'Presente' ELSE 'Ausente' END estado
FROM Asistencia_UPC.registros_asistencia ra
JOIN Asistencia_UPC.materias m ON m.materia_id = ra.materia_id
JOIN Asistencia_UPC.profesores p ON p.profesor_id = m.profesor_id
JOIN Asistencia_UPC.estudiantes e ON e.estudiante_id = ra.estudiante_id;

-- ============================================================
-- AUDITORIA (auditoria unificada de Oracle, sin triggers)
-- Registra cada INSERT/UPDATE/DELETE: quien, cuando, desde que equipo,
-- con que programa, la sentencia y sus valores. Nadie la puede alterar.
-- Los registros quedan en la vista del sistema UNIFIED_AUDIT_TRAIL.
-- ============================================================
CREATE AUDIT POLICY pol_auditoria_asistencia
    ACTIONS INSERT ON Asistencia_UPC.profesores, UPDATE ON Asistencia_UPC.profesores, DELETE ON Asistencia_UPC.profesores,
            INSERT ON Asistencia_UPC.estudiantes, UPDATE ON Asistencia_UPC.estudiantes, DELETE ON Asistencia_UPC.estudiantes,
            INSERT ON Asistencia_UPC.materias, UPDATE ON Asistencia_UPC.materias, DELETE ON Asistencia_UPC.materias,
            INSERT ON Asistencia_UPC.materia_estudiantes, UPDATE ON Asistencia_UPC.materia_estudiantes, DELETE ON Asistencia_UPC.materia_estudiantes,
            INSERT ON Asistencia_UPC.registros_asistencia, UPDATE ON Asistencia_UPC.registros_asistencia, DELETE ON Asistencia_UPC.registros_asistencia;

AUDIT POLICY pol_auditoria_asistencia;

-- ============================================================
-- PERMISOS DE SOLO LECTURA para el auditor
-- ============================================================
GRANT SELECT ON Asistencia_UPC.profesores TO auditor;
GRANT SELECT ON Asistencia_UPC.estudiantes TO auditor;
GRANT SELECT ON Asistencia_UPC.materias TO auditor;
GRANT SELECT ON Asistencia_UPC.materia_estudiantes TO auditor;
GRANT SELECT ON Asistencia_UPC.registros_asistencia TO auditor;
GRANT SELECT ON Asistencia_UPC.vista_asistencia_detallada TO auditor;

-- ============================================================
-- VERIFICACION (deben salir 5 tablas, 1 vista y la politica activa)
-- ============================================================
SELECT table_name FROM all_tables WHERE owner = 'ASISTENCIA_UPC' ORDER BY table_name;
SELECT view_name FROM all_views WHERE owner = 'ASISTENCIA_UPC';
SELECT policy_name, enabled_option, success, failure
  FROM audit_unified_enabled_policies
 WHERE policy_name = 'POL_AUDITORIA_ASISTENCIA';

--------------------------------------------------------------------------------
-- Conexion de la aplicacion:  Asistencia_UPC / UPC123 @ localhost:1521/XEPDB1
-- Conexion del auditor:       auditor / Auditor.123 @ localhost:1521/XEPDB1
-- (contraseñas estándar: cámbialas por las tuyas; si cambias la de
--  Asistencia_UPC, ponla tambien en .streamlit/secrets.toml)
--
-- Consultas del auditor:
--   -- Historial de cambios (puede tardar unos segundos en aparecer)
--   SELECT event_timestamp, client_identifier AS usuario_app, dbusername,
--          os_username, userhost AS equipo, client_program_name AS programa,
--          action_name AS operacion, object_name AS tabla, sql_text, sql_binds
--     FROM unified_audit_trail
--    WHERE object_schema = 'ASISTENCIA_UPC'
--    ORDER BY event_timestamp DESC;
--
--   -- Asistencia legible
--   SELECT * FROM Asistencia_UPC.vista_asistencia_detallada ORDER BY fecha_hora DESC;
--
-- OPCIONAL: ver la auditoria como vista dentro del esquema Asistencia_UPC.
-- Ejecutar conectado como SYS AS SYSDBA:
--   GRANT SELECT ON SYS.UNIFIED_AUDIT_TRAIL TO Asistencia_UPC;
--   CREATE OR REPLACE VIEW Asistencia_UPC.auditoria AS
--   SELECT event_timestamp fecha, action_name operacion, object_name tabla,
--   client_identifier usuario_app, dbusername usuario_bd, os_username usuario_so,
--   userhost equipo, client_program_name programa, sql_text, sql_binds valores,
--   return_code codigo_error
--   FROM SYS.UNIFIED_AUDIT_TRAIL WHERE object_schema = 'ASISTENCIA_UPC';
--   GRANT SELECT ON Asistencia_UPC.auditoria TO auditor;
--------------------------------------------------------------------------------
