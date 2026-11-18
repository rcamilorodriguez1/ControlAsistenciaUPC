CREATE OR REPLACE TRIGGER trg_matricula_activa
BEFORE INSERT OR UPDATE ON materia_estudiantes FOR EACH ROW
DECLARE v_n NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_n FROM estudiantes WHERE estudiante_id=:NEW.estudiante_id AND activo=1;
    IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20087,'Estudiante inactivo o inexistente.'); END IF;
    SELECT COUNT(*) INTO v_n FROM materias m JOIN profesores p ON p.profesor_id=m.profesor_id
    WHERE m.materia_id=:NEW.materia_id AND m.activo=1 AND p.activo=1;
    IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20087,'Materia o profesor inactivo.'); END IF;
END;
/
CREATE OR REPLACE TRIGGER trg_asistencia_activa
BEFORE INSERT ON registros_asistencia FOR EACH ROW
DECLARE v_n NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_n FROM estudiantes WHERE estudiante_id=:NEW.estudiante_id AND activo=1;
    IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20087,'Estudiante inactivo.'); END IF;
    SELECT COUNT(*) INTO v_n FROM materias m JOIN profesores p ON p.profesor_id=m.profesor_id
    WHERE m.materia_id=:NEW.materia_id AND m.activo=1 AND p.activo=1;
    IF v_n<>1 THEN RAISE_APPLICATION_ERROR(-20087,'Materia o profesor archivado.'); END IF;
END;
/
CREATE OR REPLACE VIEW v_eventos_gestion AS
SELECT evento_id,entidad,entidad_id,accion,motivo,actor_rol,actor_id,ocurrido_en FROM eventos_gestion;
