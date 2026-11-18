-- Contadores monotonicos: no dependen de la resolucion del reloj del sistema.
CREATE OR REPLACE TRIGGER trg_profesores_actualizado
BEFORE UPDATE ON profesores FOR EACH ROW
BEGIN :NEW.actualizado_en:=SYSTIMESTAMP; :NEW.version_edicion:=:OLD.version_edicion+1; END;
/
CREATE OR REPLACE TRIGGER trg_estudiantes_actualizado
BEFORE UPDATE ON estudiantes FOR EACH ROW
BEGIN :NEW.actualizado_en:=SYSTIMESTAMP; :NEW.version_edicion:=:OLD.version_edicion+1; END;
/
CREATE OR REPLACE TRIGGER trg_materias_actualizado
BEFORE UPDATE ON materias FOR EACH ROW
BEGIN :NEW.actualizado_en:=SYSTIMESTAMP; :NEW.version_edicion:=:OLD.version_edicion+1; END;
/
