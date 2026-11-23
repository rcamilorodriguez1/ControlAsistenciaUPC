# Sentencias para la exposición de Base de Datos

1. Abrir `01_consultas_para_exponer.sql`: inventario, diccionario, FK, JOIN,
   agregados, vistas, paquetes, triggers y compilación. Solo lectura.
2. Usar `02_consultas_con_parametros.sql` para una materia/clase elegida por el
   equipo. En SQL Developer, seleccionar un SELECT, F9 y completar sus binds.
3. Las consultas se ejecutan como propietario del esquema del proyecto. El catálogo
   `USER_*` muestra el esquema de la conexión; cambiar CURRENT_SCHEMA no cambia USER.
4. Las filas visibles en la demostración dependerán de la base a la que se conecte.
   El paquete para compartir contiene metadatos, no una exportación de personas.

El directorio de SQL original contiene instalación, migraciones y laboratorios.
Esas tareas están separadas del guion de solo lectura: para mostrar el modelo
no hay que reinstalar el esquema existente. El DDL consolidado se importa en
Data Modeler como estructura; la instalación de la aplicación usa sus scripts versionados.
