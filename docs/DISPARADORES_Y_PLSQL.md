# Justificación de disparadores y primera entrega PL/SQL

Decisión: 11 de noviembre de 2026. Cambio de esquema: **001 → 002**.
Implementación: `sql/migraciones/002_auditoria.sql`. Este documento explica propósito, eventos,
datos registrados, límites y cómo demostrar cada disparador desde SQL*Plus.

## Ampliación 006: administración y concurrencia

`TRG_ADMINISTRADORES_ACTUALIZADO` actúa antes de cada UPDATE de ADMINISTRADORES y asigna
`ACTUALIZADO_EN=SYSTIMESTAMP`. Mantiene la fecha del perfil técnico de aplicación incluso
si se actualiza desde SQL*Plus; no copia contraseñas al historial ni concede permisos.

Los tres disparadores existentes de actualización de PROFESORES, ESTUDIANTES y MATERIAS
ahora también incrementan `VERSION_EDICION` desde el valor anterior. El paquete administrativo
bloquea la fila y exige esa versión antes de guardar: evita que dos editores se sobrescriban,
incluidas actualizaciones SQL directas. Se usa un contador porque el reloj de un sistema puede
asignar la misma marca temporal a varias actualizaciones rápidas.

Las instantáneas de edición se registran en `EVENTOS_GESTION` desde `PKG_ADMINISTRACION`,
dentro de la transacción, con motivo e identidad del administrador. Los disparadores de
asistencia y matrículas existentes aceptan también ese rol. No se crea un trigger genérico que
copie hashes ni biometría. La auditoría de edición administrativa corresponde a operaciones
del paquete; el propietario Oracle conserva sus permisos de desarrollo y no es un archivo
inmutable frente a DBA. Ver [ADMINISTRACION.md](ADMINISTRACION.md).

## Problema que resuelve

La asistencia original conserva únicamente el estado actual. Una corrección o eliminación no
dejaba evidencia del estado anterior, y retirarse de una materia eliminaba la matrícula sin historial.
Además, los perfiles y materias tenían fecha de creación pero no de actualización.

Se eligen disparadores porque estas acciones deben quedar registradas tanto desde Python como
desde SQL*Plus y SQL Developer. Las reglas simples continúan en PK, FK, UNIQUE y CHECK;
las operaciones con motivo y validaciones se ofrecen mediante paquetes PL/SQL.

## Objetos nuevos

| Objeto | Función |
| --- | --- |
| `AUDITORIA_ASISTENCIA` | Instantáneas de correcciones y eliminaciones, actor declarado y motivo. |
| `HISTORIAL_MATRICULAS` | Eventos ALTA y RETIRO con identificación de la matrícula. |
| `ACTUALIZADO_EN` | Columna con zona horaria en PROFESORES, ESTUDIANTES y MATERIAS. |
| `PKG_AUDITORIA` | Contexto por sesión: rol, identificador y motivo; funciones de consulta y limpieza. |
| `PKG_ASISTENCIA`, versión 002 | Conserva sus firmas anteriores y añade corrección, eliminación y retiro. |
| `V_AUDITORIA_ASISTENCIA`, `V_HISTORIAL_MATRICULAS` | Consultas de presentación sin contraseñas ni vectores biométricos. |

Las tablas de historial no tienen FK hacia las entidades operativas: una baja del profesor,
materia o estudiante no debe borrar el historial ni impedir que se audite una baja en cascada.
Conservan identificadores y valores del evento; no copian nombres, hashes, imágenes, audio ni embeddings.
No se reconstruyen eventos pasados: el historial empieza al aplicar la migración.

## 1. TRG_ASISTENCIA_AUD — correcciones y bajas

- **Tabla:** REGISTROS_ASISTENCIA.
- **Evento:** AFTER UPDATE OR DELETE, por cada fila.
- **Condición:** en UPDATE, solo registra si cambian presencia, materia, estudiante o instante.
  Una sentencia que vuelve a asignar los mismos valores no añade un evento.
- **Acción:** inserta en AUDITORIA_ASISTENCIA el ID del registro, operación, datos anteriores y
  nuevos, momento del evento, usuario Oracle, actor declarado, motivo y metadatos de conexión.
  En DELETE los valores nuevos quedan nulos.
- **Justificación:** permite explicar que una asistencia pasó de ausente a presente o por qué
  se eliminó. También registra modificaciones SQL directas y eliminaciones por cascada.
- **Límite:** una inserción inicial no produce evento en esta tabla: el registro operativo ya
  representa esa toma. La auditoría está orientada a cambios posteriores.

Ejemplo: `PKG_ASISTENCIA.CORREGIR_ASISTENCIA` cambia 0 por 1 con el motivo
"Evidencia revisada" y el disparador conserva ambos valores.

## 2. TRG_MATRICULAS_HIST — altas y retiros

- **Tabla:** MATERIA_ESTUDIANTES.
- **Evento:** AFTER INSERT OR DELETE, por cada fila.
- **Acción:** crea un evento ALTA o RETIRO en HISTORIAL_MATRICULAS, con materia, estudiante,
  fecha original de matrícula, fecha del evento y contexto del actor.
- **Justificación:** una reinscripción posterior no oculta que antes existió un retiro. No se
  usa un contador de estudiantes que pueda quedar desactualizado: las estadísticas siguen siendo consultas.
- **Límite:** una eliminación en cascada genera un RETIRO técnico; no se interpreta automáticamente
  como una decisión voluntaria del estudiante. El motivo/contexto permiten explicar la operación.
  No se admite cambiar el significado del historial atribuyendo un actor que no fue comunicado.
  Los UPDATE directos de las claves de matrícula no están cubiertos por este trigger: un cambio
  de materia debe expresarse como retiro y nueva matrícula. Restringir esa edición directa queda
  para la capa de servicios y la separación futura de permisos.

## 3. TRG_PROFESORES_ACTUALIZADO — modificación docente

- **Tabla:** PROFESORES.
- **Evento:** BEFORE UPDATE, por cada fila.
- **Acción:** asigna SYSTIMESTAMP a ACTUALIZADO_EN.
- **Justificación:** deja constancia de la última sentencia de modificación del perfil o sus credenciales,
  sin guardar el hash anterior en una bitácora.
- **Límite:** no indica qué campo cambió y se ejecuta incluso si UPDATE asigna el mismo valor.

## 4. TRG_ESTUDIANTES_ACTUALIZADO — modificación estudiantil

- **Tabla:** ESTUDIANTES.
- **Evento:** BEFORE UPDATE, por cada fila.
- **Acción:** actualiza ACTUALIZADO_EN.
- **Justificación:** permite saber cuándo se modificó el perfil o se renovó su representación biométrica.
  No duplica la biometría en el historial.
- **Límite:** no constituye una medición de calidad biométrica ni invalida por sí mismo la caché del modelo;
  esa integración sigue pendiente en el roadmap.

## 5. TRG_MATERIAS_ACTUALIZADO — modificación de materia

- **Tabla:** MATERIAS.
- **Evento:** BEFORE UPDATE, por cada fila.
- **Acción:** actualiza ACTUALIZADO_EN.
- **Justificación:** muestra cuándo se editaron nombre, código, sección o profesor asignado.
- **Límite:** no registra una historia completa de esos campos. Se conserva la unicidad del código con UNIQUE.

Los tres disparadores de fecha sobreescriben una fecha suministrada manualmente: la base determina
el momento de actualización. En filas ya existentes la nueva columna parte del instante de migración,
porque no conocemos una fecha real de modificación anterior.

## Transacciones, identidad y pool

Ningún disparador hace COMMIT ni utiliza transacciones autónomas. Si se revierte la acción, se
revierte su historial. Si falla la escritura del historial, falla también la sentencia que lo origina;
no se ocultan errores con WHEN OTHERS THEN NULL. Se auditan cambios confirmados, no intentos fallidos.

El usuario Oracle compartido es UPC_ASISTENCIA. Para distinguir un profesor de otro, la app debe
comunicar su sesión autenticada a PKG_AUDITORIA al adquirir una conexión y limpiar ese contexto
antes de devolverla al pool. Las operaciones sin contexto se registran como **NO_IDENTIFICADO**,
con el usuario Oracle real, sin inventar un profesor responsable.

Ese enlace ya está incorporado en `bd.py`: toma el rol y perfil de la sesión iniciada de Streamlit,
limpia cualquier contexto anterior y establece el actor antes de ejecutar la operación. Al devolver
la conexión limpia el contexto también si hubo error. Si no puede limpiarlo, descarta esa conexión.
Las herramientas sin sesión de Streamlit no atribuyen sus acciones a un profesor o estudiante.

El contexto es **identidad declarada**, no una autenticación independiente: SQL*Plus usa las mismas
credenciales del propietario y puede declarar un actor o modificar sus propias tablas. La protección
contra manipulación por el dueño del esquema exigiría cuentas/permisos separados; no se promete aquí.
El paquete comprueba que el actor exista y que el profesor declarado sea dueño de la materia al
corregir/eliminar, pero la autenticación de esa persona sigue correspondiendo a la aplicación.

Ejemplo manual con un profesor existente, reemplazando 123 por su ID:

```sql
BEGIN
    pkg_auditoria.establecer_contexto('PROFESOR', 123, 'Revision de evidencia');
END;
/
```

Al terminar la sesión lógica:

```sql
BEGIN
    pkg_auditoria.limpiar_contexto;
END;
/
```

El estado de paquetes no se deshace por ROLLBACK; por eso la limpieza es explícita en éxito y error.
Los triggers solo usan :OLD/:NEW y getters del paquete; no consultan las tablas que están modificando.

## Primera entrega de PL/SQL

`sql/09_paquete_auditoria.sql` utiliza estado de paquete, procedimientos, funciones y validaciones.
`sql/11_paquete_asistencia.sql` utiliza parámetros, %TYPE, SELECT INTO, bloqueo FOR UPDATE,
errores de aplicación y excepciones propagadas. Las operaciones nuevas son:

| Procedimiento | Acción |
| --- | --- |
| `CORREGIR_ASISTENCIA(id, presente, motivo)` | Exige profesor declarado, propiedad de materia y motivo; actualiza presencia. |
| `ELIMINAR_ASISTENCIA(id, motivo)` | Valida el mismo contexto y elimina con motivo auditable. |
| `RETIRAR_ESTUDIANTE(estudiante, materia, motivo)` | Permite retiro al propio estudiante declarado o al profesor de la materia. |

Los procedimientos no confirman la transacción. El llamador decide COMMIT o ROLLBACK. Los motivos
temporales de estas operaciones se restauran incluso si ocurre un error. Las firmas originales de
matricular, registrar y calcular porcentaje se mantienen para no romper consumidores anteriores.

## Instalación y SQL*Plus

Una instalación nueva ejecuta `oracle_scripts.sql`, registra 001 y aplica 002. Una base existente
001 utiliza la migración, no el instalador que exige un esquema vacío.

Si al usuario existente le falta CREATE TRIGGER, el administrador debe concederlo en XEPDB1:

```bat
sqlplus / as sysdba
```

```sql
ALTER SESSION SET CONTAINER = XEPDB1;
@sql/00_habilitar_disparadores.sql
```

Después, desde CMD como usuario del proyecto:

```bat
.venv\Scripts\python.exe scripts\oracle.py migrar
.venv\Scripts\python.exe scripts\oracle.py verificar
.venv\Scripts\python.exe scripts\oracle.py demostrar-disparadores
.venv\Scripts\python.exe scripts\oracle.py exportar
```

Equivalente conectado como UPC_ASISTENCIA en SQL*Plus:

```sql
@sql/migraciones/002_auditoria.sql
@sql/04_verificar.sql
@sql/12_demostracion_disparadores.sql
```

Usar una sesión nueva y detener la app al migrar: Oracle confirma DDL implícitamente y reemplazar
paquetes puede invalidar estado de sesiones existentes. La migración no borra filas, crea solo lo
que falta y puede reejecutarse tras un fallo. No sustituye silenciosamente objetos existentes con
estructuras incompatibles: la compilación/verificación debe fallar y se revisa la causa. 002 solo se
registra después de compilar y verificar todos sus objetos; una reejecución no duplica esa fila.
Iniciar SQL*Plus desde la raíz del proyecto: en este cliente 18c se usan rutas `@sql/...` para
evitar la terminación observada al resolver `@@../...` entre directorios anidados.

## Demostración y aceptación

`12_demostracion_disparadores.sql` crea fixtures únicos dentro de una transacción, ejecuta los cinco
triggers, muestra corrección/eliminación y alta/retiro con un cursor FOR, y revierte las filas y
el historial al terminar. No contiene datos reales ni DDL. Los contadores IDENTITY pueden avanzar
aunque se reviertan las filas. No ejecutar COMMIT entre los pasos de esa demostración.

La aceptación incluye cambios directos sin contexto, UPDATE sin cambios, rollback del historial,
eliminaciones en cascada, limpieza del contexto de conexiones y rechazo de correcciones de otra materia.
La exportación DDL incorpora los dos paquetes antes de los cinco triggers para respetar dependencias.

### Verificación realizada el 11 de noviembre de 2026

- Migración 001 → 002 aplicada a UPC_ASISTENCIA en XEPDB1 y repetida correctamente: la segunda
  ejecución no duplicó la versión ni borró filas.
- Ocho tablas, nueve vistas, dos paquetes con sus cuerpos y cinco triggers válidos y activos;
  USER_ERRORS sin registros.
- **17 pruebas aprobadas**, incluida integración Oracle de todos los casos anteriores, motivos
  Unicode, conservación de zona horaria y uso del rol/perfil de Streamlit tras cerrar sesión.
- Demostración ejecutada desde SQL*Plus: mostró UPDATE 0→1, DELETE 1→NULL y eventos ALTA/RETIRO;
  después revirtió fixtures e historial.
- Diagnóstico Python correcto, dependencias sin conflictos declarados y pantallas de inicio/acceso
  docente sin excepciones con AppTest.
- Las cinco tablas funcionales y las dos de historial quedaron sin filas al terminar las pruebas.
- DDL exportado y revisado: cinco FK posteriores a las tablas, dos paquetes antes de los cinco
  triggers y sin nombre fijo del esquema de origen.

Estos resultados corresponden a la entrega 002. La entrega 003 incorpora el modelo de clases y
las pantallas de revisión manual; la conexión final de SQL Developer continúa pendiente.

## Propuestas documentadas pero diferidas

- **Normalizar códigos con BEFORE INSERT/UPDATE:** requiere definir si el código será insensible a
  mayúsculas y ajustar también búsquedas de la app, además de resolver posibles códigos existentes
  que colisionen al normalizarlos. No se aplica en 002.
- **Bloquear asistencia de clases cerradas:** implementado en 003 mediante `TRG_ASISTENCIA_CLASE`,
  el estado de `CLASES` y la confirmación en `PKG_CLASES`. La reapertura autorizada sigue pendiente.

## Ampliación 003: clases y revisión inicial

La instalación actual incorpora dos disparadores más: `TRG_ASISTENCIA_CLASE` protege las altas
en clases confirmadas y la identidad/revisión inicial de las filas; `TRG_CLASES_IDENTIDAD` impide
reabrir o alterar la identidad y la confirmación original. `TRG_ASISTENCIA_AUD` amplía sus instantáneas
para conservar el ID de clase y los datos de la revisión inicial al corregir o borrar registros.

La justificación de cada acción y la separación entre restricciones, procedimientos y triggers
están en [CLASES_Y_REVISION.md](CLASES_Y_REVISION.md). El nuevo laboratorio es
`scripts/oracle.py demostrar-clases`; el laboratorio 002 continúa disponible y compatible.

## Ampliación 005: cuentas y materias archivadas

Se añaden dos disparadores. La base actual tiene nueve en total, manteniendo los cinco de 002
y los dos de 003. La migración 004 amplió los existentes sin agregar otros.

| Disparador | Acción que lo ejecuta | Justificación |
| --- | --- | --- |
| TRG_MATRICULA_ACTIVA | BEFORE INSERT OR UPDATE de MATERIA_ESTUDIANTES | Rechazar una matrícula si el estudiante, la materia o su docente no están activos. Protege también INSERT directo, además de PKG_GESTION. |
| TRG_ASISTENCIA_ACTIVA | BEFORE INSERT de REGISTROS_ASISTENCIA | Rechazar nuevas asistencias de personas o materias archivadas. No bloquea consultas ni borra la historia previa. |

La condición depende de varias tablas; un CHECK de una sola fila no cubre esa consulta.
Los triggers no hacen COMMIT ni generan transacciones autónomas. No se ejecutan en DELETE,
para conservar el funcionamiento de los retiros y las cascadas heredadas sin consultar una
tabla padre mientras se está modificando. No sustituyen la autorización de PKG_GESTION/PKG_CLASES
ni impiden que el propietario Oracle deshabilite controles.

Para el archivo y la retirada biométrica se eligieron procedimientos explícitos en PKG_GESTION:
la aplicación solicita una acción con motivo y el procedimiento valida el actor, aplica cambios
y registra EVENTOS_GESTION dentro de la misma transacción. Un trigger que interpretara cualquier
UPDATE como consentimiento o petición de archivo no tendría esa información. Los códigos se
normalizan en los servicios y procedimientos, con índices únicos sobre expresiones normalizadas;
no se añade un trigger de normalización silenciosa. La propuesta antigua anterior se resolvió así.

Las pruebas Oracle cubren permiso, motivos, duplicados, cuentas archivadas, retiro con asistencia
previa, eliminación de vectores y rollback final de fixtures. Políticas: [REGLAS_NEGOCIO.md](REGLAS_NEGOCIO.md).

## Referencias

- [Oracle: disparadores DML y valores OLD/NEW](https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/dml-triggers.html).
- [Oracle: directrices de diseño de triggers](https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/trigger-design-guidelines.html).
- [Oracle: transacciones autónomas y su independencia del rollback principal](https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/autonomous-transactions.html).
