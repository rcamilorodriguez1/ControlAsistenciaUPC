# Cuentas, matrícula, archivo y biometría

Implementación del punto 3 de la revisión, 11 de noviembre de 2026. Esquema 005.

## Identificadores y acceso

Los usuarios docentes se guardan en minúsculas y los códigos de materias e institucionales
en mayúsculas. Se recortan espacios externos, se normaliza texto Unicode y se rechazan
controles y campos excesivos. Los códigos admiten letras ASCII, números, punto, guion y guion
bajo; empiezan por letra o número. Los índices únicos también protegen la base ante registros
simultáneos y diferencias de mayúsculas. Nombres iguales están permitidos: no identifican personas.

| Campo | Límite |
| --- | --- |
| Usuario docente | 100 caracteres |
| Código de materia o institucional | 50 caracteres |
| Nombre | 200 caracteres |
| Sección | 100 caracteres |
| Motivo de gestión | 1–500 caracteres, obligatorio |
| Contraseña bcrypt | 8–72 bytes UTF-8, sin carácter nulo |

El registro docente incluye un medidor local de fortaleza y confirmación en vivo.
La valoración es orientativa y no modifica por sí sola los requisitos anteriores;
se sigue comprobando la coincidencia al registrar. Ver [FRONTEND.md](FRONTEND.md).

El código institucional es obligatorio en las altas nuevas desde la aplicación. Los perfiles
heredados pueden mantener NULL al migrar para conservar sus datos; deben completarse por
administración, sin inventar un código a partir del nombre. No se verifica automáticamente
la pertenencia del código a una institución: hace falta una fuente institucional para acreditarlo.

El registro docente requiere autorización además de los campos habituales. La clave privada
se configura como `PROFESOR_CLAVE_ALTA`; la generada en este PC está en
`.local/ALTA_DOCENTE.md`. No es la contraseña de Oracle ni debe incorporarse al repositorio.
`scripts/preparar_alta_docente.py` prepara esa configuración sin sobrescribir la existente.
Una cuenta con credenciales directas de propietario Oracle mantiene privilegios administrativos;
la autorización del formulario no limita a ese propietario.

Cinco fallos de contraseña bloquean ese usuario durante quince minutos. La ventana de intentos
dura quince minutos y un acceso correcto limpia el contador. `LIMITES_ACCESO` conserva una
huella SHA-256 del usuario, fechas y contador; no guarda contraseñas ni el nombre en claro.
Los datos antiguos de esta tabla se depuran al intentar acceder. No es un límite global por IP.

La sesión vence tras treinta minutos sin interacción o a las ocho horas desde el acceso.
Las operaciones comprueban la vigencia y la identidad; cerrar sesión o caducar elimina capturas,
resultados y widgets de autenticación. No hay cierre visual por temporizador: una pestaña ociosa
puede seguir mostrando la pantalla anterior hasta su próxima interacción, que vuelve a validar.

## Matrícula e historial

`PKG_GESTION` centraliza crear materias, matricular, retirar, archivar y retirar biometría.
El docente debe estar activo y ser propietario; el estudiante solo puede gestionar su cuenta
y matrícula. El contexto `SISTEMA`, disponible al administrador SQL, permite archivar cuentas
y retirar biometría. La matrícula y el retiro requieren contexto docente o estudiante.

La retirada de una materia elimina su matrícula actual y agrega el historial de retiro;
las asistencias previas permanecen. El archivo de estudiante retira sus matrículas, desactiva
la cuenta y elimina sus vectores, conservando clases, asistencias e historial. Archivar docente
desactiva su cuenta y sus materias. Archivar materia la retira de operaciones activas sin borrar
su historia; repetir ese archivo no genera otro evento.

Los disparadores rechazan nuevas matrículas y asistencias si las cuentas o materias están
inactivas. `PKG_CLASES` también rechaza abrir o confirmar clases de materias archivadas.
`EVENTOS_GESTION` registra entidad, acción, motivo, actor e instante; no incluye los vectores.
Los reportes históricos docentes siguen consultando las asistencias de materias archivadas.

Las acciones están disponibles en **Administrar cuenta e historial**, con motivo y confirmación.
Retirar biometría o archivar la cuenta propia cierra la sesión. Al retirar biometría se pierde
el acceso facial: la asistencia podrá resolverse manualmente por el docente y un futuro
reingreso biométrico requerirá un procedimiento administrativo de actualización autorizado.
Desde 008 puede utilizarse, si está aprobada y vigente, la alternativa de documento y contraseña.
Una cuenta archivada sigue sin poder acceder. Ver [EXCEPCIONES_BIOMETRICAS.md](EXCEPCIONES_BIOMETRICAS.md).

Las FK heredadas mantienen `ON DELETE CASCADE` para compatibilidad de scripts anteriores;
la aplicación utiliza archivo y no ofrece DELETE físico de cuentas o materias. Un propietario
que ejecute DELETE directamente puede destruir datos académicos. No usarlo como sustituto de
`PKG_GESTION`. La separación entre propietario y cuenta de ejecución sigue pendiente del bloque
de despliegue; el contexto de auditoría actual confía en la aplicación que posee esas credenciales.

## Transacciones y conservación biométrica

Las escrituras Python no reintentan automáticamente un COMMIT de resultado incierto.
Se cierran cursores y se revierte cualquier trabajo pendiente antes de devolver la conexión,
además de limpiar el contexto de auditoría. Los procedimientos de archivo y retirada biométrica
utilizan SAVEPOINT y rollback ante errores; el COMMIT pertenece al cliente. Las lecturas conservan
reintentos de conexión; no se reintentan errores de validación o integridad.

Solo se guardan vectores, no fotografías ni audio de registro. Las capturas temporales viven
en la sesión hasta descartarlas, confirmar o cerrarla. Las plantillas activas se conservan mientras
la cuenta esté activa y el titular no solicite retirarlas; no hay eliminación por edad ni se ha
definido un plazo institucional para el historial académico. Ese plazo deberá acordarse antes
de un despliegue real. La retirada desde Python invalida la caché facial del proceso actual;
tras cambios directos por SQL, reiniciar la aplicación y sus demás procesos para descartar cachés.

Las copias nuevas están cifradas y siguen la [política de recuperación y retención](RECUPERACION.md).
Una retirada no reescribe copias previas; antes de promover una restauración hay que volver a
aplicar las retiradas y archivos posteriores a la fecha del respaldo, usando un registro de esas
solicitudes conservado aparte del respaldo. Un respaldo tampoco sustituye esa gestión.
