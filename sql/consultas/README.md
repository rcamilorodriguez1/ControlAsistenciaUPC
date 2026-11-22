# Catálogo SQL de UPC Aula

Las consultas de la aplicación se organizan aquí por módulo y operación. El lector común
es `src/base_datos/consultas.py`; las carpetas `base_datos/` y `servicios/` corresponden a
los módulos consumidores. `compartidas/` reúne sentencias idénticas utilizadas en varios flujos.

Esta carpeta es un catálogo de ejecución, no una instalación SQL*Plus. Los archivos conservan
las sentencias y sus parámetros `:nombre`; el driver recibe los valores por separado.
Los bloques PL/SQL conservan su terminador interno y las consultas SQL no necesitan `/`.
El esquema se instala con `oracle_scripts.sql` y `sql/migraciones/`.

`cargar_sql()` valida la ruta y mantiene una caché de lectura por proceso.
`sql_con_identificadores()` admite exclusivamente nombres Oracle para las plantillas de
esquema/objeto; no admite valores de formularios ni fragmentos SQL arbitrarios. Los datos
siguen usando parámetros enlazados, incluso cuando la consulta utiliza una plantilla.

La organización inicial extrae 104 apariciones de SQL de nueve módulos, agrupadas en
88 sentencias únicas, más dos plantillas para esquema/objeto. No cambia reglas, contratos
de paquetes, formularios ni COMMIT/ROLLBACK. El código que genera DDL a partir de metadatos
de respaldos sigue identificado como herramienta técnica y conserva sus validaciones.

La decisión de trasladar más reglas a procedimientos, funciones, paquetes, vistas o
disparadores se revisará en el [segundo roadmap](../../docs/ROADMAP_2.md).
