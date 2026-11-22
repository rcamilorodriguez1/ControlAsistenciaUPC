# Cuenta Oracle de ejecución separada del propietario

Punto 4 del [primer roadmap](ROADMAP.md), completado el 22 de noviembre de 2026.
UPC_AULA_APP está creado y verificado en Autonomous con esquema UPC_ASISTENCIA, 53
permisos comprobados, 55 sentencias analizadas y cero objetos propios. Se conserva el
ensayo previo con una cuenta temporal en XE. La conexión local actual del portal no se
cambió y no se instaló una nueva versión de tablas.

## Tres cuentas técnicas y tres roles web

| Cuenta Oracle | Responsabilidad | Uso |
| --- | --- | --- |
| `UPC_ASISTENCIA` | Propietario de tablas, vistas, paquetes y disparadores. | Instalación, migraciones, mantenimiento y alta web inicial explícita. |
| `UPC_AULA_APP` | Ejecución con permisos directos limitados. | Accesos web, sesiones y operaciones docentes/estudiantiles actuales. |
| `UPC_ADMIN_APP` | Ejecución administrativa limitada existente. | Paquetes y vistas autorizados para Gestión académica. |

Profesor, estudiante y administrador siguen siendo roles de la aplicación. No reciben
contraseñas técnicas Oracle. El acceso web administrativo verifica su credencial mediante
el pool principal, como antes; sus operaciones de gestión utilizan el pool administrativo.

## Resolver el esquema sin obtener sus privilegios

`ORACLE_USUARIO` identifica al usuario conectado; `ORACLE_ESQUEMA` identifica al propietario.
La configuración de producción propuesta es:

```toml
ORACLE_USUARIO = "UPC_AULA_APP"
ORACLE_ESQUEMA = "UPC_ASISTENCIA"
ORACLE_ADMIN_USUARIO = "UPC_ADMIN_APP"
```

Las claves permanecen en el perfil privado. `src/base_datos/esquema.py` valida el nombre y
configura `Connection.current_schema` mediante el callback del pool y al adquirir una
conexión. Esto permite resolver `profesores` como `UPC_ASISTENCIA.profesores`, sin cambiar
SESSION_USER ni otorgar permisos adicionales. Se restaura el esquema al reutilizar conexiones.
La conexión administrativa construye sus nombres con el propietario explícito.

Las instalaciones locales anteriores conservan la compatibilidad: si no se define
ORACLE_ESQUEMA, se usa ORACLE_USUARIO como propietario. El arranque de producción, en
cambio, exige propietario y dos cuentas de ejecución distintos.

Las comprobaciones del esquema y de la clave HMAC consultan `ALL_*` filtrando el propietario;
no confunden los objetos propios vacíos del runtime con las tablas de negocio. El respaldo
y la restauración rechazan una conexión cuyo SESSION_USER no coincide con CURRENT_SCHEMA,
antes de crear una copia vacía o intentar DDL. El mantenimiento debe usar su perfil propietario.

## Contrato de permisos

La fuente es [07_permisos_ejecucion.sql](../sql/cloud/07_permisos_ejecucion.sql).
Contiene 28 GRANT: 17 permisos de objeto y 36 permisos de columna, 53 autorizaciones
comprobadas en total. Se cuentan por separado las columnas de una misma sentencia.

| Recurso | Permiso necesario |
| --- | --- |
| Profesores | SELECT, INSERT de usuario/nombre/hash y UPDATE de contraseña para recuperación. |
| Estudiantes | SELECT e INSERT de los campos de alta; sin UPDATE directo de cuenta. |
| Materias, matrículas y clases | SELECT; las escrituras se realizan mediante los paquetes existentes. |
| Registros de asistencia | SELECT e INSERT de los cuatro campos que necesita la compatibilidad vigente. |
| Administradores | SELECT para verificar el acceso web; sin INSERT, UPDATE ni DELETE. |
| Verificación estudiantil | SELECT, INSERT del identificador y UPDATE de estado, fecha, factores y versión. Sin cambios directos de aprobación, documento o contraseña excepcional. |
| Sesiones | SELECT, INSERT de los campos del broker de recuperación y UPDATE de revocación. |
| Límites de intentos | SELECT, INSERT de clave, UPDATE de intentos/ventana/bloqueo y DELETE para limpieza. |
| Eventos de gestión | INSERT de los campos de bitácora; sin lectura, edición ni borrado directo. |
| Versiones de esquema | SELECT. |
| Paquetes | EXECUTE en AUDITORIA, ASISTENCIA, CLASES, GESTION y SESIONES. |

La cuenta solo necesita CREATE SESSION como privilegio de sistema, sin roles, cuota,
objetos propios, ANY ni GRANT OPTION. No recibe los paquetes ADMINISTRACION/EXCEPCIONES
ni acceso directo a AUDITORIA_ASISTENCIA/HISTORIAL_MATRICULAS. Las escrituras internas de
los paquetes y disparadores conservan sus derechos de propietario y sus validaciones.

`src/base_datos/permisos_ejecucion.py` compara los grants reales de objeto y columna con
el contrato. El preflight rechaza diferencias, privilegios de sistema adicionales, roles,
usuario/esquema incorrectos y fallos de las comprobaciones de esquema o administración.

**Límite:** se separa ejecución de propiedad y DDL. La cuenta todavía puede leer datos de
varias cuentas web y efectuar el DML concedido; la autorización por persona sigue en los
servicios, sesiones y paquetes existentes. El contexto de auditoría sigue siendo una
declaración del backend de confianza. Esto no añade seguridad por fila ni vuelve inmutable
el historial frente al propietario. El rediseño de reglas y paquetes pertenece al segundo roadmap.

## Preparación en Autonomous desde el PC

El preparador utiliza el descriptor y las credenciales propietarias ya guardadas en
`.local/oracle_cloud/`. No copia esas claves al código ni modifica `.streamlit/secrets.toml`.

```powershell
.\.venv\Scripts\python.exe scripts\preparar_ejecucion_cloud.py --comprobar-plan
.\.venv\Scripts\python.exe scripts\preparar_ejecucion_cloud.py
```

La segunda orden pide ADMIN sin eco en la terminal. Verifica que la cuenta no exista,
guarda la clave nueva en un archivo privado antes del DDL, crea UPC_AULA_APP con CREATE
SESSION y concede los permisos desde UPC_ASISTENCIA. Rechaza sustituir cuentas o claves.
ADMIN no queda guardado. No ejecutar los bloques parametrizados de creación pegándolos
sin preparar sus binds; el preparador es quien enlaza la clave.

Si Oracle devuelve ORA-01017 al autenticar ADMIN, revisar la contraseña de ese usuario
definida al crear Autonomous UPCAULA. Antes de superar esa conexión no se generan las
credenciales de ejecución ni se crean usuarios. El diagnóstico del 22/11 distingue ese
rechazo de los accesos del propietario y de UPC_AULA_APP; no imprime credenciales ni
reintenta automáticamente la autenticación.

Archivos privados resultantes:

- `.local/oracle_cloud/credenciales_tecnicas.toml`: conserva el perfil propietario original.
- `.local/oracle_cloud/credenciales_ejecucion.toml`: perfil de ejecución y administración
  limitada, sin la contraseña propietaria.
- `.local/oracle_cloud/ejecucion_verificada.json`: identidad, número de permisos y consultas
  analizadas; no contiene contraseñas ni filas de personas.

Comprobación posterior, sin DDL ni DML:

```powershell
.\.venv\Scripts\python.exe scripts\preparar_ejecucion_cloud.py --verificar
```

Comprueba cuenta, esquema, sistema, roles, objetos propios, cuota, versiones y contrato.
Analiza las sentencias de ejecución con Cursor.parse, sin ejecutar sus operaciones. Nunca
envía DDL a parse, porque Oracle sí lo ejecutaría. Esto no sustituye el ensayo transaccional.

Si la cuenta se creó y se interrumpió la concesión de permisos:

```powershell
.\.venv\Scripts\python.exe scripts\preparar_ejecucion_cloud.py --continuar
```

Primero autentica la clave original y luego reaplica los grants. No revoca excesos ni
restablece claves automáticamente. Si la creación o CREATE SESSION quedaron incompletos,
conservar los archivos y revisar el estado con ADMIN: no borrar el perfil para generar otro.

## Alta administrativa y operación

La cuenta runtime no puede crear administradores. Para una base cloud sin cuenta web
administrativa, el operador puede usar explícitamente el perfil propietario desde el PC:

```powershell
.\.venv\Scripts\python.exe scripts\crear_administrador.py --config-oracle .local\oracle_cloud\credenciales_tecnicas.toml --usuario admin.upc --nombre "Administración UPC"
```

Es una operación del punto 5; esta preparación no la ejecuta automáticamente. Solicita
la contraseña web sin eco y rechaza sustituir una cuenta existente. El perfil solo afecta
al proceso de esa herramienta. No guardar el perfil propietario en la configuración normal
del contenedor ni conceder permisos adicionales al runtime para hacer mantenimiento.

En la futura configuración del servidor usar credenciales_ejecucion.toml como fuente de
los campos Oracle y completar aparte dominio, autorización docente y clave HMAC original.
La cuenta técnica cloud ya está activada y verificada. Incorporar ese perfil al servidor
y completar el ensayo de los portales en producción sigue pendiente de configuración y VM.

## Verificación y referencias

El ensayo Oracle crea una cuenta local temporal `UPC_RUN_…`, aplica el mismo contrato,
comprueba permisos y rechazos, ejecuta un flujo sintético de clase/perfil y prueba preflight
y reutilización del pool. Revierte sus filas y retira solo esa cuenta sin objetos, sin CASCADE.
El perfil normal del portal y sus contraseñas permanecen intactos.

El 22/11 el usuario ejecutó el preparador definitivo y comunicó el resultado correcto.
Se contrastó con `.local/oracle_cloud/ejecucion_verificada.json`: usuario UPC_AULA_APP,
esquema UPC_ASISTENCIA, 53 permisos, 55 sentencias analizadas, cero objetos propios y
verificado=true. Existe su perfil privado. La contraseña ADMIN no se guardó.

Pruebas: `tests/test_cuenta_ejecucion.py`, `tests/test_ejecucion_oracle.py` y
`tests/test_despliegue.py`. Evidencias privadas en `.local/ejecucion/`.

- [Oracle: crear usuarios en Autonomous](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/manage-users-create.html).
- [python-oracledb: current_schema](https://python-oracledb.readthedocs.io/en/latest/api_manual/connection.html#oracledb.Connection.current_schema).
- [python-oracledb: callbacks del pool](https://python-oracledb.readthedocs.io/en/latest/user_guide/connection_handling.html#session-callbacks-for-setting-pooled-connection-state).
