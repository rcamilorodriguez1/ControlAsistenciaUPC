# Excepciones de verificación de identidad — esquema 009

Actualización 011: el [documento identifica al alumno desde el registro](DOCUMENTO_ESTUDIANTIL.md).
Se retira el código institucional de los formularios y el acceso de prueba usa documento.
Las cuentas anteriores completan su documento desde el perfil o Gestión académica.

Actualización 010: se añade un [modo académico temporal con clave común](PRUEBA_ACADEMICA.md)
para cualquier estudiante activo, incluso sin excepción. Utiliza código institucional,
estado `PRUEBA_ACADEMICA` y auditoría diferenciada. El flujo autorizado por documento
descrito a continuación conserva sus reglas.

Implementado el 17 de noviembre de 2026. Aplicación: UPC | Aula.

## Política y alcance

El acceso biométrico estudiantil existente comprueba **un rostro**. La voz es opcional en el
registro y se utiliza en asistencia: tener su plantilla guardada no significa que se haya
comprobado como segundo factor de acceso. Actualmente no hay una política configurable de dos
o tres factores de autenticación. Esta entrega conserva la política facial efectiva; definir
otra combinación y sus pruebas es un trabajo separado.

Los profesores y administradores conservan su acceso por contraseña y sus restricciones.
La excepción se aplica al estudiante, que es el rol cuyo acceso actualmente depende de biometría.
Se utiliza el servicio compartido de sesiones: mismo rol, caducidad, navegación y sesión única.

El documento identifica la cuenta; **no autentica por sí solo**. La alternativa requiere:

1. Comprobación del documento por un docente autorizado o un administrador activo.
2. Autorización explícita, categoría de excepción, referencia del expediente y vigencia.
3. Documento más contraseña alternativa al iniciar sesión.

El sistema valida su correspondencia con lo registrado y autorizado. No consulta un registro
gubernamental ni certifica automáticamente la autenticidad de la cédula presentada.
La categoría puede ser física, médica, técnica o administrativa. No se solicitan diagnósticos,
fotocopias ni informes médicos en este formulario.

## Autorización docente y entrega manual (009)

Decisión del 22/11: se sustituye el envío por correo por entrega manual de la clave.
No se requiere correo del estudiante, proveedor de correo ni dominio remitente.

### Clave compartida para las pruebas

Por petición del usuario, se prepara una clave de pruebas en
`.local/ALTA_ESTUDIANTE.md`, equivalente al archivo privado de alta docente.
El docente utiliza esa misma clave al autorizar individualmente a los alumnos de
prueba en **Excepciones de acceso**. Cada alumno accede con su propio documento y
la clave acordada; se mantienen su autorización, vigencia y revocación en Oracle.
La contraseña queda en el archivo privado, excluido del repositorio.

En **Portal docente → Excepciones de acceso**, el profesor selecciona una materia
propia activa y un alumno activo matriculado, comprueba su documento y establece
una contraseña de al menos 12 caracteres. Indica categoría, referencia y vigencia
(1 día por defecto; entre 1 y 365). Confirma la clave y la entrega personalmente.
El formulario limpia documento y contraseña después de autorizar; el sistema guarda
solo HMAC del documento, últimos cuatro caracteres y hash bcrypt de la contraseña.

Puede renovar o revocar las autorizaciones que emitió. No puede sustituir las de
Administración ni las de otro docente, incluso si comparte matrícula con el alumno.
Administración puede revisar y sustituir una autorización docente. Una clave perdida
se sustituye mediante renovación; no se recupera desde Oracle.

`PKG_EXCEPCIONES_DOCENTES` valida rol, cuenta activa, propiedad de materia, matrícula,
versión y autoría. La cuenta técnica restringida recibe EXECUTE en el paquete; el
runtime ordinario conserva sus 53 permisos y no recibe DML de autorización. La sesión
real se vuelve a validar antes de usar esa conexión, sin adoptar el rol administrador.

009 añade `autorizado_docente_por` y `materia_autorizacion_id`, con claves foráneas,
y amplía la restricción de aprobación: administrador o docente con materia, nunca
ambos. Conserva las aprobaciones previas. La renovación administrativa limpia el
aprobador docente. No añade tablas ni elimina datos académicos.

Se comprobaron acceso, vigencia, revocación, autoría, matrícula y sesión en Oracle
local con cuentas sintéticas. Autonomous 009 y sus permisos se verificaron tras un
respaldo cifrado. El ensayo con el profesor y estudiante en Render sigue pendiente.

## Operación

En **Gestión académica → Verificación**, el administrador puede consultar, filtrar y exportar
los estados; autorizar o renovar una excepción; crear un estudiante sin rostro ni voz; y revocar.
Para una cuenta existente debe seleccionarla expresamente, sin volver a crearla. No se reactiva
una cuenta archivada mediante este procedimiento.

Al autorizar se indican tipo de documento (CC, TI, CE o PA), número, categoría, referencia del
expediente, vigencia de 1–365 días y contraseña de al menos 12 caracteres, con límite bcrypt de
72 bytes UTF-8. Se exige confirmar la contraseña y declarar que el documento fue comprobado.
La contraseña se entrega al estudiante por un canal institucional privado; no puede recuperarse
en texto desde el sistema. Para sustituirla, el administrador renueva la autorización.

En **Portal del estudiante → No puedo completar la validación biométrica**, el estudiante introduce
documento y contraseña. El formulario está disponible sin abrir la cámara y permanece accesible
ante errores faciales. Una sesión de otro rol debe cerrarse antes de autenticar otra cuenta.
Tras cinco fallos se bloquea ese identificador durante quince minutos; el error no revela si la
cuenta existe o si está autorizada. El bloqueo y su contador persisten en Oracle.

Autorizar, renovar o revocar invalida las sesiones anteriores del estudiante. El vencimiento se
comprueba tanto al entrar como al validar una sesión activa. Un cambio concurrente de cuenta,
contraseña o autorización impide utilizar una prueba de acceso anterior.

## Dos datos distintos

| Dato | Significado |
| --- | --- |
| `excepcion_activa` + `expira_en` | Permiso vigente para utilizar el método alternativo |
| `estado_verificacion` + `verificado_en` | Resultado y fecha de la última verificación que abrió sesión |
| `PENDIENTE` | Todavía no se registró un acceso con esta versión del sistema |
| `BIOMETRICA_COMPLETA` | Se comprobó el método facial exigido por la política actual (1/1) |
| `EXCEPCIONAL` | Se abrió sesión mediante la alternativa autorizada (0/1 factores biométricos) |

Una autorización no marca automáticamente al estudiante como ya verificado. Una revocación
conserva el resultado histórico del último acceso. Un posterior acceso facial cambia el último
estado a completo, sin borrar la historia de excepciones ni desactivar su autorización.
Las cuentas previas no se marcan como completas por tener una plantilla guardada.

El portal y Mi perfil muestran el método de acceso. La consola distingue el último resultado
de las autorizaciones vigentes y permite filtrar ambos por separado.

## Persistencia, auditoría y protección

`verificacion_estudiantes` contiene la autorización, estado, fecha, cantidades de factores,
versión de credencial, aprobador y referencia. Tiene clave foránea al estudiante y al aprobador,
unicidad de documento y restricciones que impiden excepciones activas sin credencial/aprobación.

El documento completo no se almacena. Se normalizan espacios, puntos y guiones, conservando
ceros iniciales. Se guarda HMAC-SHA-256 de tipo y número y sus últimos cuatro caracteres para
mostrarlos enmascarados. La contraseña se almacena con bcrypt. Los reportes y el paquete de
consulta no devuelven hashes ni plantillas biométricas.

La clave HMAC es independiente de la clave de cifrado de respaldos. Por defecto está en
`.local/claves/identidad.key` (configurable mediante `IDENTIDAD_CLAVE_RUTA`; rutas relativas
se resuelven desde la raíz del proyecto). Nunca debe publicarse ni mostrarse en capturas.
**Conservar una copia privada de la clave original junto con el plan de recuperación.**
El respaldo de Oracle no incluye este archivo. Restaurar los datos en otro PC también exige
restaurar esta clave. Si existen documentos registrados, el preparador rechaza generar una
clave nueva en sustitución de una perdida.

`PKG_EXCEPCIONES` exige contexto de administrador activo para consultar, autorizar y revocar.
La conexión administrativa limitada recibe EXECUTE, sin SELECT/DML directo sobre esta tabla.
El paquete no ofrece una operación que pueda fingir un acceso biométrico correcto.

Los servicios emiten una prueba firmada de 90 segundos, de un solo uso. El broker comprueba
firma, cuenta, versión, método, credencial y autorización en la misma transacción que abre la
sesión, siguiendo el orden de bloqueo sesión → verificación → cuenta. Un rechazo hace rollback
del reemplazo, preservando la sesión previa. El perfil guardado en Streamlit solo conserva los
datos de presentación, sin contraseña, hash, prueba ni vectores.

En `eventos_gestion`, entidad `VERIFICACION`, se registran:

- `EXCEPCION_AUTORIZADA` y `EXCEPCION_REVOCADA`, con administrador y expediente/motivo.
- `CREDENCIAL_VALIDADA`, comprobación alternativa previa a abrir sesión.
- `ACCESO_VERIFICADO`, resultado confirmado junto con la sesión, método y factores.
- `VALIDACION_FALLIDA`, intentos fallidos, límites, muestras inválidas, fallos técnicos y pruebas rechazadas.

Antes de autenticar, el actor es SISTEMA; el identificador de entidad es el estudiante objetivo
cuando se conoce, o 0 si todavía es desconocido. No se incluyen documento completo, contraseña,
hash, imagen, audio ni detalles del motor biométrico. Los campos administrativos de referencia
y motivo deben contener información administrativa, sin diagnósticos ni documentos personales.
Si Oracle no puede guardar un fallo, queda un aviso técnico mínimo en el logger. No se concede
un acceso que no pueda confirmar su estado y auditoría en la base de datos.

La excepción de acceso **no registra asistencia automáticamente**, no cambia porcentajes y no
concede permisos de profesor o administrador. Las muestras ausentes continúan como SIN_MUESTRA;
la revisión manual de asistencia por el docente conserva sus reglas y trazabilidad.

## Instalación y consultas

Actualización de una instalación existente (respaldo privado previo automático):

```powershell
.\.venv\Scripts\python.exe scripts\oracle.py migrar
.\.venv\Scripts\python.exe scripts\oracle.py verificar
```

El instalador nuevo incluye 009. Si se ejecuta el SQL directamente con SQL*Plus, como propietario
del proyecto y desde su raíz, aplicar 008 después de 007 y `@sql/migraciones/009_excepciones_docentes.sql` después de 008;
preparar la clave con `.\.venv\Scripts\python.exe scripts\preparar_identidad.py`.
Una instalación con rol administrativo de nombre personalizado requiere EXECUTE sobre
`pkg_excepciones` y `pkg_excepciones_docentes` para dicho rol; `scripts/oracle.py` lo concede desde la configuración existente.
El script de preparación administrativa exige ahora 009.

Consultas de presentación en SQL*Plus/SQL Developer, como propietario:

```sql
SELECT NVL(v.estado_verificacion,'PENDIENTE') estado, COUNT(*) cantidad
FROM estudiantes e LEFT JOIN verificacion_estudiantes v ON v.estudiante_id=e.estudiante_id
GROUP BY NVL(v.estado_verificacion,'PENDIENTE');

SELECT estudiante_id, estado_verificacion, excepcion_activa,
       autorizado_por, expira_en, verificado_en,
       factores_verificados, factores_requeridos
FROM verificacion_estudiantes ORDER BY estudiante_id;

SELECT evento_id, entidad_id, accion, actor_rol, actor_id, ocurrido_en, motivo
FROM eventos_gestion WHERE entidad='VERIFICACION' ORDER BY evento_id;
```

## Verificación y límites de aceptación

Las pruebas utilizan cuentas y documentos sintéticos propios, con limpieza por ID. Cubren acceso
sin ninguna biometría, alta excepcional, claves incorrectas y bloqueo, vencimiento de sesiones,
revocación, documento repetido, versión obsoleta, pruebas repetidas/ausentes/manipuladas, retorno
al método facial, permisos administrativos, conflictos de rol y limpieza de secretos en sesión.
La revisión de Brave utiliza un servidor y perfil aislados, sin conexiones Oracle ni cuentas reales.

La comprobación con personas, documentos y procedimientos institucionales reales corresponde al
ensayo final. La implementación y sus pruebas automáticas no equivalen a aceptación del usuario.

Resultados del 17 de noviembre:

- **217 pruebas aprobadas**, Oracle habilitado y sin omisiones: `.local/pruebas_excepciones_completas_final.log`.
- SQL*Plus verificó 001–008, restricciones, paquetes válidos y ausencia de errores de compilación.
- **12 vistas nuevas** en Brave, a 1440, 768, 390 y 320 px, sin errores/desbordamiento de página:
  `.local/frontend/6f17f011b384/resultado.json`.
- **12 vistas anónimas de la instancia HTTPS existente**, incluidas regresiones de los otros accesos:
  `.local/frontend/ff5df33f8cc6/resultado.json`.
- Restauración completa en dos esquemas temporales: 14 tablas, ocho versiones, dos estados de
  verificación recuperados y sesiones restauradas revocadas. Los esquemas se eliminaron al terminar:
  `.local/ensayos/76D3DD47D0A3/resultado.json`.

## Archivos principales

| Área | Archivos |
| --- | --- |
| Credenciales y pruebas | `src/servicios/verificacion_identidad.py`, `src/servicios/excepciones_biometricas.py` |
| Sesiones compartidas | `src/servicios/sesiones_servidor.py`, `src/utilidades/sesiones.py`, `sql/32_paquete_sesiones.sql` |
| Interfaz | Componentes `acceso_excepcional.py`, `gestion_excepciones.py`, `estado_verificacion.py`; pantallas de estudiante, administrador y perfil |
| Perfil y errores | Repositorio/servicio de perfil y `src/base_datos/administracion.py` |
| Oracle | Migración `008_excepciones.sql`, `34_paquete_excepciones.sql`, `35_verificar_excepciones.sql`, instalador, verificador y permisos administrativos |
| Preparación y recuperación | `scripts/preparar_identidad.py`, `oracle.py`, `diagnostico.py`, preparación administrativa, ensayo de restauración y cargador `recuperacion.py` |
| Pruebas | `test_verificacion_identidad.py`, `test_excepciones_oracle.py`, `test_excepciones_interfaz.py`, fixtures, regresiones y comprobador visual |

Se actualizaron también la configuración de ejemplo, README, roadmap y guías relacionadas.
