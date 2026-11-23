-- Ejecutar desde la raiz del proyecto; scripts/oracle.py establece ese directorio.
SET ECHO OFF
SET VERIFY OFF
SET DEFINE OFF
SET SERVEROUTPUT ON
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
@sql/01_tablas.sql
@sql/02_vistas.sql
@sql/03_paquete_asistencia.sql
@sql/04_verificar.sql
@sql/07_registrar_version.sql
@sql/migraciones/002_auditoria.sql
@sql/migraciones/003_clases.sql
@sql/migraciones/004_estados_deteccion.sql
@sql/migraciones/005_gestion.sql
@sql/migraciones/006_administracion.sql
@sql/migraciones/007_sesiones.sql
@sql/migraciones/008_excepciones.sql
@sql/migraciones/009_excepciones_docentes.sql
@sql/migraciones/010_prueba_academica.sql
@sql/migraciones/011_documento_estudiantil.sql
PROMPT Instalacion inicial completada. No se insertaron personas ni muestras biometricas.
