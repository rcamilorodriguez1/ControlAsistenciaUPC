-- Entrada para SQL*Plus y SQL Developer (Run Script / F5).
-- Conectarse PRIMERO como el usuario de la aplicacion al PDB correcto.
-- No crea usuarios ni elimina objetos; solo instala sobre un esquema vacio.
-- Desde la raiz: sqlplus -L /nolog
-- SQL> CONNECT UPC_ASISTENCIA@"//localhost:1521/XEPDB1"
-- SQL> @oracle_scripts.sql
@@sql/instalar.sql
