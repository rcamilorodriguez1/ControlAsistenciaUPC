# Aprender la base de UPC Aula, paso a paso

Decisión: vaciar las dos bases y cargar nuevos datos gradualmente, entendiendo
cada operación. La estructura permanece en 001–011. La prueba de la página y cámara
la realiza el usuario.

## Primer paso: distinguir estructura y datos

Una tabla es la estructura que define columnas y reglas. Sus filas son los datos.
Podemos eliminar las filas sin eliminar la tabla, su PK, FK, índices o triggers.

- **Oracle local, XEPDB1:** base en este PC, utilizada para desarrollo y ensayos.
- **Oracle Autonomous, UPCAula:** base en la nube a la que se conecta Render.

Tienen la misma estructura y datos independientes. Ejecutar un script en una no
lo ejecuta en la otra. Commit/push publican código; no sincronizan filas Oracle.

Las cuentas técnicas UPC_ASISTENCIA, UPC_AULA_APP y UPC_ADMIN_APP permiten conectar
y operar. Los profesores, estudiantes y administradores de la web son filas dentro
de las tablas de aplicación. Borrar estas filas no elimina los usuarios Oracle.

## Script de la limpieza autorizada

`scripts/limpiar_datos_pruebas.py` no instala ni recrea Oracle. Sin `--aplicar`
consulta los conteos. Con esa opción hace lo siguiente:

1. Lee cada perfil privado TOML. Sus contraseñas no aparecen en consola.
2. Comprueba propietario, identidad de la base, 14 tablas exactas y versiones 001–011.
3. Bloquea las tablas para evitar escrituras durante la limpieza.
4. Crea y verifica un respaldo cifrado independiente por base. Primero prepara
   todos los respaldos; después comienza a eliminar filas.
5. Ejecuta DELETE en 13 tablas, empezando por hijas y terminando por historiales.
6. Comprueba cero filas, versiones conservadas, objetos válidos y triggers activos.
7. Ejecuta COMMIT tras verificar ambos destinos y guarda un informe privado.

La información se guarda en `.local/reinicios/`. Cada respaldo incluye la estructura
y los datos anteriores cifrados. La clave de recuperación permanece privada.

### Por qué importa el orden

Una autorización puede apuntar a estudiante, docente, materia y administrador.
Se elimina antes que esas cuentas. Las asistencias se eliminan antes que sus
clases. Las matrículas se eliminan antes que estudiantes y materias.

Los triggers siguen habilitados y pueden generar auditoría durante los DELETE.
Por eso los historiales se vacían al final. No se desactivan restricciones para
forzar un borrado ni se dejan tablas sin protección.

### DELETE, COMMIT y ROLLBACK

```sql
DELETE FROM registros_asistencia;
```

Esta sentencia elimina filas de la tabla. La tabla y sus reglas siguen existiendo.
Durante la transacción, el cambio está pendiente. COMMIT lo confirma y ROLLBACK
revierte lo que todavía no se haya confirmado. El script conserva respaldos para
recuperar el estado anterior después de confirmar.

Las dos bases tienen transacciones independientes: no se promete un COMMIT
distribuido atómico. Se verifican ambas antes de confirmar y el informe registra
la confirmación de cada destino; los respaldos permiten recuperar ante un fallo.

`VERSIONES_ESQUEMA` conserva sus 11 filas porque describen la estructura instalada.
No son alumnos ni clases. Borrarlas haría que el preflight no reconociera la base.
Los contadores internos de identidades se conservan; empezar con datos vacíos no
exige que el siguiente ID sea 1.

## Ruta de estudio y carga gradual

| Paso | Scripts/objetos que estudiaremos | Qué debemos entender antes de seguir |
| --- | --- | --- |
| 1 | `limpiar_datos_pruebas.py` y respaldo/recuperación | Estructura, datos, dos destinos, transacciones y restauración. |
| 2 | `scripts/crear_administrador.py` | Diferencia entre usuario Oracle y cuenta web; INSERT, bcrypt y auditoría. No crea usuarios Oracle. |
| 3 | Registro docente y `sql/01_tablas.sql` | Primera fila docente, PK, identidad, usuario y contraseña protegida. |
| 4 | Registro estudiantil, `sql/41_paquete_gestion_documentos.sql` | Cuenta más documento en una transacción; HMAC, unicidad y campos obligatorios. |
| 5 | Crear materia y matricular | Relación 1:N, tabla puente N:M, FK y PK compuesta. |
| 6 | `sql/25_paquete_clases_gestion.sql` | BORRADOR, propuesta, confirmación completa, bloqueos y reintentos. |
| 7 | Vistas y `sql/consultas/` | SELECT, WHERE, JOIN, GROUP BY, COUNT y diferencia entre tabla/vista. |
| 8 | Triggers de `10`, `19`, `24` y `31` | Fechas/versiones, actividad, identidad y conservación de historia. |
| 9 | `sql/32_paquete_sesiones.sql` y servicios de identidad | Token, sesión, caducidad, cuenta activa y autorización. |
| 10 | `sql/42`, `43` y `44` | Edición administrativa y excepciones por documento; permisos y autoría. |
| 11 | `scripts/oracle.py`, `sql/instalar.sql`, migraciones 002–011 | Orden de instalación, CREATE/ALTER, recompilación y verificación. |
| 12 | Scripts cloud y preflight | Propietario/runtime/admin, permisos, configuración y Render. |

En cada paso revisaremos propósito, entradas, tablas afectadas, validaciones,
sentencia principal, transacción y resultado esperado. Primero se explica y
después se añade un conjunto pequeño de datos acordado con el usuario.

Las versiones antiguas de paquetes conservan la evolución del proyecto. Las
definiciones vigentes se obtienen siguiendo `sql/instalar.sql` y las migraciones;
no se suman todas las versiones como si fueran objetos diferentes.
