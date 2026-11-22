# Rama: base de datos y aporte académico

Depende del [roadmap general](ROADMAP.md). Goodwill aclarado por el usuario:
**valor, beneficios y aporte académico**.

| ID | Entregable y criterio de cierre | Estado |
| --- | --- | --- |
| BD1 | Visualización de tablas y relaciones, navegable sin credenciales ni registros personales | Pendiente |
| BD2 | Diccionario con columnas, tipos, nulabilidad, claves y reglas, contrastado con el esquema instalado | Pendiente |
| BD3 | Guía de conexión: navegador, Render, driver/pools, TLS, Oracle y separación de cuentas | Pendiente |
| BD4 | Goodwill: problema, valor por actor, beneficios medibles, aporte académico y límites | Pendiente |

## Fuentes y continuidad

- [Base de datos](BASE_DE_DATOS.md): diccionario y relaciones existentes.
- [SQLPlus y SQL Developer](SQLPLUS_Y_SQLDEVELOPER.md): inspección y conexión de desarrollo.
- [Cuenta de ejecución](CUENTA_EJECUCION.md): propietario, runtime y cuenta técnica restringida.
- [Despliegue](DESPLIEGUE.md): Oracle Autonomous y Render.

Las ampliaciones de esquema deben tener migración versionada, comprobación de
compilación y permisos y pruebas de aislamiento. Mantener los datos académicos al
migrar. No incluir contraseñas, DSN privados, vectores ni documentos en la documentación.
