# Rama: base de datos y aporte académico

Depende del [roadmap general](ROADMAP.md). Goodwill aclarado por el usuario:
**valor, beneficios y aporte académico**.

| ID | Entregable y criterio de cierre | Estado |
| --- | --- | --- |
| BD1 | Visualización de tablas y relaciones, navegable sin credenciales ni registros personales | Terminado: [catálogo interactivo](base_datos/index.html), 14 tablas y 11 FK |
| BD2 | Diccionario con columnas, tipos, nulabilidad, claves y reglas, contrastado con el esquema instalado | Terminado: [140 columnas de Autonomous 009](DICCIONARIO_DATOS.md) |
| BD3 | Guía de conexión: navegador, Render, driver/pools, TLS, Oracle y separación de cuentas | Terminado: [guía de conexión](CONEXION_BASE_DATOS.md) |
| BD4 | Goodwill: problema, valor por actor, beneficios medibles, aporte académico y límites | Terminado: [valor y aporte académico](GOODWILL.md) |

## Fuentes y continuidad

- [Base de datos](BASE_DE_DATOS.md): diccionario y relaciones existentes.
- [SQLPlus y SQL Developer](SQLPLUS_Y_SQLDEVELOPER.md): inspección y conexión de desarrollo.
- [Cuenta de ejecución](CUENTA_EJECUCION.md): propietario, runtime y cuenta técnica restringida.
- [Despliegue](DESPLIEGUE.md): Oracle Autonomous y Render.

Las ampliaciones de esquema deben tener migración versionada, comprobación de
compilación y permisos y pruebas de aislamiento. Mantener los datos académicos al
migrar. No incluir contraseñas, DSN privados, vectores ni documentos en la documentación.
