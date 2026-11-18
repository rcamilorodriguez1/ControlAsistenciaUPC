-- Solo consultas: no crea personas ni cambia asistencias.
SET SERVEROUTPUT ON
SELECT * FROM v_profesores;
SELECT * FROM v_estudiantes;
SELECT * FROM v_materias;
SELECT * FROM v_materia_estudiantes;
SELECT * FROM v_registros_asistencia;
SELECT * FROM v_resumen_materias;
BEGIN
    DBMS_OUTPUT.PUT_LINE('Porcentaje sin registros: '
        || pkg_asistencia.porcentaje_asistencia(-1));
END;
/
