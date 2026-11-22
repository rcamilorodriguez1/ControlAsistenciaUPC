SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
SET SERVEROUTPUT ON
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM versiones_esquema WHERE version='006';
    IF n<>1 OR USER IN ('SYS','SYSTEM') THEN RAISE_APPLICATION_ERROR(-20210,'Se requiere 006 y el propietario del proyecto.'); END IF;
    SELECT COUNT(*) INTO n FROM user_tables WHERE table_name='SESIONES_USUARIO';
    IF n=0 THEN EXECUTE IMMEDIATE q'~CREATE TABLE sesiones_usuario (
        rol VARCHAR2(20 CHAR) NOT NULL, actor_id NUMBER NOT NULL, token_hash VARCHAR2(64 CHAR) NOT NULL,
        creada_en TIMESTAMP WITH TIME ZONE NOT NULL, actividad_en TIMESTAMP WITH TIME ZONE NOT NULL,
        expira_en TIMESTAMP WITH TIME ZONE NOT NULL, revocada_en TIMESTAMP WITH TIME ZONE,
        CONSTRAINT pk_sesiones_usuario PRIMARY KEY(rol,actor_id),
        CONSTRAINT ck_sesiones_rol CHECK(rol IN ('PROFESOR','ESTUDIANTE','ADMINISTRADOR')),
        CONSTRAINT ck_sesiones_actor CHECK(actor_id>0 AND actor_id=TRUNC(actor_id)),
        CONSTRAINT ck_sesiones_hash CHECK(REGEXP_LIKE(token_hash,'^[a-f0-9]{64}$','c')),
        CONSTRAINT ck_sesiones_fechas CHECK(expira_en>creada_en AND actividad_en>=creada_en))~'; END IF;
END;
/
@sql/32_paquete_sesiones.sql
COMMENT ON TABLE sesiones_usuario IS 'Una sesion vigente por rol/cuenta. Solo SHA-256 del token, nunca el token original ni contrasenas.';
BEGIN
    EXECUTE IMMEDIATE 'GRANT EXECUTE ON pkg_sesiones TO UPC_ROL_ADMIN';
EXCEPTION WHEN OTHERS THEN IF SQLCODE<>-1917 THEN RAISE; END IF;
END;
/
@sql/36_recompilar_esquema.sql
@sql/33_verificar_sesiones.sql
INSERT INTO versiones_esquema(version,descripcion)
SELECT '007','Sesiones unicas en servidor, revocacion y caducidad para los tres roles' FROM dual
WHERE NOT EXISTS(SELECT 1 FROM versiones_esquema WHERE version='007');
COMMIT;
PROMPT Sesiones 007 instaladas sin borrar cuentas ni datos academicos.
