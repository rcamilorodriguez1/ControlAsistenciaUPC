SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
SET SERVEROUTPUT ON
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM versiones_esquema WHERE version='007';
    IF n<>1 OR USER IN ('SYS','SYSTEM') THEN
        RAISE_APPLICATION_ERROR(-20300,'Se requiere 007 y el propietario del proyecto.');
    END IF;
    SELECT COUNT(*) INTO n FROM user_tables WHERE table_name='VERIFICACION_ESTUDIANTES';
    IF n=0 THEN EXECUTE IMMEDIATE q'~CREATE TABLE verificacion_estudiantes (
        estudiante_id NUMBER CONSTRAINT pk_verificacion_est PRIMARY KEY,
        documento_huella VARCHAR2(64 CHAR), tipo_documento VARCHAR2(2 CHAR), documento_final VARCHAR2(4 CHAR),
        clave_hash VARCHAR2(255 CHAR), excepcion_activa NUMBER(1) DEFAULT 0 NOT NULL,
        categoria VARCHAR2(20 CHAR), referencia VARCHAR2(100 CHAR),
        autorizado_por NUMBER, autorizado_en TIMESTAMP WITH TIME ZONE, expira_en TIMESTAMP WITH TIME ZONE,
        estado_verificacion VARCHAR2(25 CHAR) DEFAULT 'PENDIENTE' NOT NULL,
        verificado_en TIMESTAMP WITH TIME ZONE,
        factores_verificados NUMBER(2) DEFAULT 0 NOT NULL,
        factores_requeridos NUMBER(2) DEFAULT 1 NOT NULL,
        version_credencial NUMBER DEFAULT 0 NOT NULL,
        CONSTRAINT fk_verificacion_est FOREIGN KEY(estudiante_id) REFERENCES estudiantes(estudiante_id) ON DELETE CASCADE,
        CONSTRAINT fk_verificacion_admin FOREIGN KEY(autorizado_por) REFERENCES administradores(administrador_id),
        CONSTRAINT uq_verificacion_doc UNIQUE(documento_huella),
        CONSTRAINT ck_verificacion_huella CHECK(REGEXP_LIKE(documento_huella,'^[a-f0-9]{64}$','c')),
        CONSTRAINT ck_verificacion_tipo CHECK(tipo_documento IN ('CC','TI','CE','PA')),
        CONSTRAINT ck_verificacion_categoria CHECK(categoria IN ('FISICA','MEDICA','TECNICA','ADMINISTRATIVA')),
        CONSTRAINT ck_verificacion_activa CHECK(excepcion_activa IN (0,1)),
        CONSTRAINT ck_verificacion_estado CHECK(estado_verificacion IN ('PENDIENTE','BIOMETRICA_COMPLETA','EXCEPCIONAL')),
        CONSTRAINT ck_verificacion_factores CHECK(factores_verificados BETWEEN 0 AND 3 AND factores_requeridos BETWEEN 1 AND 3),
        CONSTRAINT ck_verificacion_version CHECK(version_credencial>=0 AND version_credencial=TRUNC(version_credencial)),
        CONSTRAINT ck_verificacion_aprobada CHECK(excepcion_activa=0 OR
            (documento_huella IS NOT NULL AND tipo_documento IS NOT NULL AND documento_final IS NOT NULL AND
             clave_hash IS NOT NULL AND categoria IS NOT NULL AND referencia IS NOT NULL AND
             autorizado_por IS NOT NULL AND autorizado_en IS NOT NULL)),
        CONSTRAINT ck_verificacion_resultado CHECK(
            (estado_verificacion='PENDIENTE' AND verificado_en IS NULL AND factores_verificados=0) OR
            (estado_verificacion='EXCEPCIONAL' AND verificado_en IS NOT NULL AND factores_verificados=0) OR
            (estado_verificacion='BIOMETRICA_COMPLETA' AND verificado_en IS NOT NULL AND factores_verificados>=factores_requeridos))
    )~'; END IF;
END;
/
COMMENT ON TABLE verificacion_estudiantes IS 'Autorizacion excepcional separada del ultimo metodo de verificacion. Documento HMAC y contraseña bcrypt; nunca documento completo.';
@sql/34_paquete_excepciones.sql
@sql/32_paquete_sesiones.sql
BEGIN
    EXECUTE IMMEDIATE 'GRANT EXECUTE ON pkg_excepciones TO UPC_ROL_ADMIN';
EXCEPTION WHEN OTHERS THEN IF SQLCODE<>-1917 THEN RAISE; END IF;
END;
/
@sql/35_verificar_excepciones.sql
INSERT INTO versiones_esquema(version,descripcion)
SELECT '008','Excepciones biometricas autorizadas, credencial alternativa y estado auditable' FROM dual
WHERE NOT EXISTS(SELECT 1 FROM versiones_esquema WHERE version='008');
COMMIT;
PROMPT Excepciones 008 instaladas sin cambiar datos biometricos ni sesiones existentes.
