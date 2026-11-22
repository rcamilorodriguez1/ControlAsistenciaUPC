SELECT USER AS usuario,
       SYS_CONTEXT('USERENV', 'DB_NAME') AS base_datos,
       SYS_CONTEXT('USERENV', 'SERVICE_NAME') AS servicio
FROM dual;
