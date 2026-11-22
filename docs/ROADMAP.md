# Primer roadmap de UPC Aula

Documentación: [índice de guías](README.md) y [registro de cambios](CAMBIOS.md).

Actualización: 22 de noviembre de 2026. Objetivo vigente: completar la organización y el
despliegue de la versión actual antes de iniciar el [segundo roadmap](ROADMAP_2.md).
El usuario confirma que tiene Autonomous Database y **todavía no tiene una VM Compute**.
La decisión vigente es ejecutar la aplicación **con Docker** en Oracle Cloud.

Objetivo: una instalación reproducible por PC, datos consistentes en Oracle, asistencia revisable,
HTTPS local y una presentación final del esquema y de PL/SQL con SQL Developer.
SQL*Plus y SQL Developer son clientes de la misma base Oracle; pasar al segundo no requiere migrar datos.

## Secuencia de trabajo y estado actual

| Orden | Entregable | Estado |
| --- | --- | --- |
| 1 | Autonomous, TLS, usuarios y esquema 001–008 | Completado: 14 tablas, 11 vistas, 10 disparadores y 7 paquetes válidos. |
| 2 | Organizar las consultas y el acceso a datos existente | Completado: catálogo SQL compartido, sin cambiar reglas ni transacciones. |
| 3 | Comprobar la reorganización | Completado: 182 pruebas aprobadas, 64 de integración omitidas y 65 consultas de lectura analizadas en Oracle Cloud. |
| 4 | Separar ejecución y administración del esquema | Completado: UPC_AULA_APP creado y verificado en Autonomous, propietario separado, 53 permisos comprobados, 55 sentencias analizadas y cero objetos propios. |
| 5 | Preparar la configuración de la aplicación para cloud | Pendiente: cuentas web iniciales, autorización docente, claves y traslado de datos si corresponde. |
| 6 | Crear VM Compute y construir/ejecutar Docker | Creación detenida por falta de capacidad A1.Flex en AD-1, AD-2 y AD-3 de Ashburn; imagen preparada, sin construcción Linux real validada. |
| 7 | Dominio, HTTPS, QR y persistencia del servidor | Red preparada según capturas y confirmaciones; conectividad, dominio, HTTPS, QR y persistencia pendientes de ensayo con la VM. |
| 8 | Ensayo completo, recuperación y presentación en SQL Developer | Pendiente. |

Guías: [despliegue](DESPLIEGUE.md), [instalación](INSTALACION.md) y
[catálogo de consultas](../sql/consultas/README.md). La aplicación mantiene por ahora su
conexión local. El primer roadmap permanece abierto hasta completar los entregables pendientes.

La organización actual mueve sentencias a archivos `.sql` y conserva el comportamiento.
Las mejoras de frontend y el rediseño de paquetes, disparadores, tablas, vistas y reglas
que deban trasladarse de Python a Oracle quedan para el **segundo roadmap**. No se crea
una migración de negocio nueva ni se da esa segunda etapa por iniciada.

## Continuación mientras no haya capacidad Compute

El usuario confirmó errores `Out of capacity` para `VM.Standard.A1.Flex` en los tres
dominios de disponibilidad de Ashburn. La VM no está creada. Esto describe los intentos
realizados; no permite conocer cuándo habrá capacidad. Se conserva la propuesta de
2 OCPU y 12 GB, sin sustituirla automáticamente por una máquina de pago.

La VCN `upc-aula-vcn` y la subred regional pública `upc-aula-publica` están creadas.
Las capturas confirman `10.0.0.0/16` para la VCN y `10.0.0.0/24` para la subred.
El formulario de la VM ya permitió activar la IP pública; no implica que haya una IP
asignada ni conectividad verificada. La puerta `upc-aula-igw` aparece Available y el usuario
confirmó la creación de la ruta `0.0.0.0/0` hacia ella en la tabla de la subred.
La captura final confirma SSH TCP 22 desde la IP administrativa `/32`, HTTP TCP 80 y
HTTPS TCP 443 públicos, y las dos reglas ICMP conservadas. La salida permite todos los
protocolos. No se incluye la IP administrativa real en la documentación compartible.

Orden propuesto para continuar el primer roadmap:

1. **Red preparada, pendiente de ensayo:** puerta de enlace y reglas revisadas mediante
   capturas, ruta confirmada por el usuario. Comprobar habilitación de la puerta,
   asociación de la tabla, SSH e Internet desde la VM cuando exista; no dar por terminada
   la conectividad antes de esa prueba.
2. **Entregable 4 completado el 22/11:** UPC_AULA_APP creado y verificado en Autonomous;
   esquema UPC_ASISTENCIA, 53 permisos de objeto/columna, 55 sentencias analizadas sin
   ejecutar sus operaciones y cero objetos propios. Se conserva el ensayo previo en XE
   y la regresión. La configuración local no se cambió; integrar este perfil en el
   servidor y probar el despliegue corresponde a los entregables siguientes.
   Guía: [cuenta de ejecución](CUENTA_EJECUCION.md).
3. **Entregable 5, preparar la configuración cloud:** preparar el perfil privado de
   producción, conservar las claves originales y definir el traslado o inicio sin datos.
   Crear las cuentas web iniciales solo contra el destino cloud explícitamente comprobado;
   mantener la instalación local mientras se acepta el resultado. Dominio e IP de la VM
   seguirán pendientes y no se sustituirán por valores ficticios en el despliegue final.
4. **Construcción Linux del entregable 6:** comprobar dependencias, modelos CPU y arranque
   del contenedor en un entorno Linux disponible. Existe el workflow manual
   `.github/workflows/contenedor.yml` para x64 y ARM64; su presencia no significa que se
   haya ejecutado. GitHub Actions puede validar la imagen sin alojar la aplicación.
5. **Preparación del entregable 8:** revisar respaldo/restauración de ensayo y preparar
   la visualización en SQL Developer con el esquema existente, sin repetir el instalador.
   El ensayo público con dispositivos y la validación final necesitan el servidor.

Al conseguir capacidad: crear la VM, comprobar SSH e Internet, añadir su IP a la ACL de
Autonomous, instalar Docker y completar dominio, HTTPS, QR y persistencia. No es necesario
mantener encendido el PC para operar la aplicación una vez desplegada en la VM.

## Seguimiento funcional e histórico

El plan original del 8 de noviembre y sus fases se conservan a continuación como registro
de las entregas, verificaciones y aceptaciones. Su numeración no sustituye la secuencia
actual de ocho entregables. Las confirmaciones del usuario siguen distinguiéndose de las
pruebas automáticas.

**Excepciones biométricas, 17 de noviembre de 2026:** implementados el acceso estudiantil alternativo
con documento/contraseña y aprobación administrativa, alta sin biometría, estado persistente,
auditoría, filtros y revocación. No se autoriza por documento solo. La política facial actual
comprueba un factor. Guía: [EXCEPCIONES_BIOMETRICAS.md](EXCEPCIONES_BIOMETRICAS.md).
Pendiente de aceptación del usuario y ensayo institucional con personas reales.

- [ ] **Entrega de la contraseña alternativa por el profesor:** el profesor la proporcionará
  al estudiante mediante correo, con una dinámica similar a `ALTA_DOCENTE`. Requisito registrado
  para una revisión posterior; el usuario indicó expresamente que todavía no se implemente.

**Mi perfil del estudiante, 17 de noviembre de 2026:** implementados el resumen acumulado,
el contador de matrículas, las materias desplegables y el calendario privado. Pendiente de
confirmación visual del usuario. Los perfiles de otros roles y Configuración siguen aplazados.
Guía y validación: [PERFIL_ESTUDIANTE.md](PERFIL_ESTUDIANTE.md). Esta vista usa el acceso
estudiantil existente y no sustituye la revisión pendiente de login institucional.

- [x] **Separador de Cerrar sesión:** alineación con el contorno del resaltado, separación
  vertical e independencia de hover/focus. El usuario confirma que quedó «perfecto»; ajuste cerrado.

**Revisión de navegación, 12 de noviembre de 2026:** implementada la separación entre inicio
público, acceso y panel por rol; menú de cuenta y conflicto entre portales con validación
en servicios compartidos. Inicio y logotipo abren la portada y conservan la identidad.
Pruebas y límites: [PORTAL_Y_SESIONES.md](PORTAL_Y_SESIONES.md). Pendiente de aceptación
del usuario. Tras la ampliación del 17 de noviembre, Mi perfil está habilitado para estudiantes;
Configuración y los perfiles de los otros roles permanecen deshabilitados.

**Confirmación del usuario, 12 de noviembre de 2026:** le gusta la identidad actual, con
ajustes futuros previstos; confirma que los iconos/contraseñas están bien y que la recuperación
docente funciona. Siguen pendientes de su confirmación los selectores y la creación de materia,
los recorridos de navegación al inicio/cierre y la presentación con zoom reducido.
El separador visual de Cerrar sesión sí está aprobado expresamente y queda fuera de esos pendientes.
Registro de aceptación: [FRONTEND.md](FRONTEND.md).

**Recuperación docente implementada:** usuario, autorización privada, contraseña nueva y
confirmación, con revocación de sesiones y límite de intentos. Detalle:
[RECUPERACION_ACCESO.md](RECUPERACION_ACCESO.md).

**Nueva revisión pendiente, por separado: acceso institucional del estudiante.** Diseñar login
general por documento/contraseña, alta controlada y vinculación con el rostro. La alternativa
autorizada ante fallos biométricos ya se implementó en 008; la recuperación de esa credencial
requiere renovación administrativa. El login institucional general continúa pendiente.
Esta revisión se acordó después de los siete puntos
originales y no está incluida entre sus entregables ya cerrados.

Ampliación implementada: sesiones únicas y revocación desde Oracle para profesor, estudiante
y administrador; logotipo/Inicio conservan la autenticación. Selectores docentes y creación
de materias corregidos. Detalle y pruebas: [PORTAL_Y_SESIONES.md](PORTAL_Y_SESIONES.md).

Hay implementaciones funcionales, visuales y de recuperación verificadas automáticamente.
La aceptación pendiente del frontend se conserva. Estos tres bloques generales siguen abiertos,
con la preparación del despliegue incorporada al punto 5:

1. **Punto 5: preparar la entrega para otro PC.** Dependencias por plataforma, instalación,
   documentación general, licencia y separación de usuarios Oracle de ejecución y administración.
2. **Punto 6: ensayo real y depuración final.** Cámara, micrófono, reconocimiento con personas,
   varias pestañas, recorrido completo, teléfono/QR, red y otro PC. Incluye calibración con datos reales.
3. **Punto 7: SQL Developer y presentación.** Conectar a la misma base, revisar el diagrama y preparar
   la demostración de tablas, restricciones, vistas, procedimientos y disparadores.

Los puntos corresponden a la última lista de trabajo. Las fases siguientes conservan la estructura
del plan original; sus números no equivalen a los de esa lista.
Frontend y validación de esta entrega: [FRONTEND.md](FRONTEND.md).

Ampliación solicitada: **tercer rol administrativo implementado**. Consulta/exportación de
auditoría y edición de cuentas/materias, con motivo, control de concurrencia e historial protegido.
Cuenta Oracle de administración separada y limitada; la separación de ejecución de profesor y
estudiante sigue en el punto 5. Acceso, permisos, credenciales privadas y pruebas:
[ADMINISTRACION.md](ADMINISTRACION.md). No añade un bloque pendiente a los puntos 5, 6 y 7.

## Orden y estado

| Fase | Entregable | Estado |
| --- | --- | --- |
| 0 | Configuración privada, usuario Oracle y SQL*Plus | Completada y verificada en el PC actual |
| 1 | Instalación, venv y HTTPS reproducibles | Herramientas iniciales listas; validación multiplataforma pendiente |
| 2 | Sesiones y flujos de interfaz consistentes | Implementada y probada automáticamente; ensayo con dispositivos pendiente |
| 3 | Reglas de negocio, clases y datos consistentes | Validaciones, archivo, límites y gestión 005 implementados y probados |
| 4 | Reconocimiento facial y de voz evaluado | Comparador y evaluador implementados; calibración con muestras reales pendiente del ensayo final |
| 5 | Rendimiento, interfaz y funcionamiento sin recursos externos | Frontend y carga implementados; mantenimiento y despliegue pendientes |
| 6 | Pruebas integrales y ensayo en otro PC | Pendiente |
| 7 | Presentación PL/SQL y SQL Developer / Data Modeler | Paquetes, disparadores y laboratorio listos; modelo visual al final |

Las fases 2–6 no se consideran resueltas por preparar la infraestructura y auditoría. Las siguientes listas
incluyen las once incidencias originales, mejoras adicionales de la auditoría y las dos ampliaciones solicitadas.

## Fase 0 — Oracle desde SQL*Plus

- [x] Retirar usuario y contraseña anteriores del código y de los scripts públicos.
- [x] Configuración central: entorno del proceso > secrets de Streamlit > valores no sensibles.
- [x] Agregar `.gitignore` para claves, certificados, entornos y resultados locales.
- [x] Preparar creación de `UPC_ASISTENCIA` sin `DROP USER`, sin permisos DBA y con cuota limitada.
- [x] Reemplazar SQL duplicado por scripts ordenados: tablas, vistas, paquete y verificación.
- [x] Rechazar instalaciones iniciales sobre esquemas no vacíos.
- [x] Agregar tabla `VERSIONES_ESQUEMA`, nombres de restricciones y comentarios de diccionario.
- [x] Confirmar acceso mediante SQL*Plus y Python, objetos válidos y conservación de zona horaria.
- [x] Exportar y revisar el DDL de la instalación resultante.
- [x] Registrar la versión solo al completar y verificar tablas, vistas y paquete PL/SQL.
- [x] Comprobar restricciones PK, FK, UNIQUE y CHECK activas y validadas.
- [x] Exportar DDL sin esquema fijo, con FK posteriores a las tablas y comentarios de diccionario.
- [x] Migración 002 reejecutable: conserva filas, compila/verifica antes de registrar versión y recupera pasos parciales.
- [x] Migraciones hasta 006 con respaldo previo; restauración V2 en destino vacío y ensayo con historial sintético.
- [x] Rol institucional mixto: auditoría/CSV y edición de cuentas/materias mediante PKG_ADMINISTRACION y conexión Oracle limitada.

Criterio de salida: `scripts/diagnostico.py` y `scripts/oracle.py verificar` terminan sin errores.
El esquema inicial conservó la interfaz de las cinco tablas de la app. La entidad de clase se
introdujo mediante la migración 003 y los estados de detección mediante 004.

## Fase 1 — Instalación por PC, entorno virtual y HTTPS

- [x] Fijar las versiones directas y el commit de los modelos faciales.
- [x] Guardar un snapshot adicional del entorno Windows / Python 3.11 auditado.
- [x] Crear venv por equipo con `preparar_entorno.cmd` o `scripts/preparar_entorno.py`.
- [x] Configurar VS Code con la carpeta `.venv`, sin rutas personales ni separadores exclusivos de Windows.
- [x] Arrancar desde el venv y desde la raíz del proyecto, independientemente del directorio de la terminal.
- [x] Preparar HTTPS real con certificado, clave y CA de desarrollo por PC.
- [x] Usar `https://localhost:8501` como URL local del QR y codificar el código de materia.
- [x] Permitir una URL LAN explícita y emitir un certificado que incluya esa IP/nombre.
- [ ] Validar cámara, micrófono y QR en el navegador con la CA local confiada.
- [ ] Validar desde un teléfono: misma red, URL del PC, firewall y CA confiada en ese dispositivo.
- [ ] Repetir instalación desde cero en Windows x64, Linux x64 y evaluar macOS/ARM.
- [ ] Resolver por plataforma los binarios de dlib y audio; documentar compilación cuando no existan wheels.
- [ ] Separar dependencias opcionales de voz e importar módulos pesados solo al utilizarlos.

Alcance honesto de “cualquier PC”: no depender del nombre del usuario ni de rutas del equipo original,
recrear el entorno y permitir configurar Oracle local o remoto. Se requieren sistema y arquitectura
compatibles, Python 3.11, dependencias nativas disponibles y una instancia Oracle accesible.
No se promete compatibilidad comprobada con sistemas que todavía no se han ensayado.

## Fase 2 — Sesiones, navegación y recursos temporales

- [x] Una función de cierre de sesión limpia rol, perfiles, fotos, claves de subida y resultados pendientes.
- [x] Vincular resultados de voz/foto a usuario, materia y toma; invalidarlos al cambiar cualquiera de ellos.
- [x] Validar otra vez el profesor, su materia y la matrícula actual en el momento de confirmar.
- [x] Corregir el cambio acceso/registro docente mediante callbacks o rerun explícito.
- [x] Unificar borrado de fotos y de claves de deduplicación en confirmar, descartar y cerrar sesión.
- [x] Distinguir archivos por contenido; limitar cantidad, bytes y resolución de fotos y bytes del audio de asistencia.
- [x] Procesar `join-code` antes de renderizar el portal; evitar abrir dos diálogos en la misma ejecución.
- [x] Mensajes para códigos inexistentes, matrícula repetida y diálogos de una sesión invalidada.
- [ ] Ensayo en navegador con cámara y micrófono reales, dos usuarios consecutivos y dos materias.
- [ ] Definir la política de caducidad por inactividad y acceso desde varias pestañas antes de exponer el sistema fuera del entorno local.

Criterio de salida: dos usuarios que comparten navegador y dos materias consecutivas no comparten
fotografías ni propuestas de asistencia. Ninguna confirmación guarda registros de otro contexto.
Implementación, comprobaciones y límites: [SESIONES.md](SESIONES.md).

## Fase 3 — Negocio y consistencia de datos

- [x] Introducir `CLASES` con identificador, materia, instante, origen y profesor responsable.
- [x] Unicidad por clase y estudiante; confirmación idempotente en Oracle y protección entre conexiones/pestañas.
- [x] Migración 003 versionada, respaldo previo y agrupación histórica conservadora, incluidos duplicados en lotes separados.
- [x] Diferenciar presente, ausente, decisión pendiente, sin muestra y análisis fallido; bloquear confirmaciones con fallo o pendientes.
- [x] Permitir corrección manual antes de confirmar, exigir motivo y guardar detección, presencia final, autor y fecha.
- [x] Auditar correcciones y eliminaciones de asistencia, y conservar historial de altas/retiros de matrícula.
- [x] Añadir ACTUALIZADO_EN y sus disparadores en profesores, estudiantes y materias.
- [x] Comunicar el actor de Streamlit al contexto Oracle y limpiarlo al adquirir/devolver conexiones.
- [x] Procedimientos PL/SQL de corrección/eliminación con motivo y retiro de matrícula con validación del actor declarado.
- [x] Validar la confirmación completa en servicios y PL/SQL: clase, rol, propiedad, matrícula, duplicados y motivos.
- [x] Extender validaciones y límites a altas y gestión de cuentas/materias; motivo obligatorio en archivo y retirada biométrica.
- [x] Código institucional obligatorio en nuevas altas; unicidad de códigos y usuarios sin distinguir mayúsculas.
- [x] Retiro conserva asistencias; archivo de cuentas/materias conserva historia y elimina biometría de cuentas estudiantiles archivadas.
- [x] Revisar transacciones, rollback, cierre de cursores y reintentos; escrituras sin repetición automática del COMMIT.
- [x] Confirmación de clase atómica con SAVEPOINT, rollback de errores y cierre de cursor; sin reintento automático del COMMIT.
- [x] Conservar offset y microsegundos al guardar/leer asistencias; verificado con una zona de sesión diferente.
- [x] Agrupar reportes por ID de clase y distinguir horario académico del instante de análisis.
- [x] Centralizar apertura/confirmación en `PKG_CLASES`; probar reintentos y concurrencia real en Oracle.
- [x] Integrar creación de materias, matrícula, retiro y archivo mediante PKG_GESTION; conservar compatibilidad SQL heredada explícita.

Criterio de salida: una clase tiene una única asistencia revisable por estudiante, incluso con
reintentos o uso de voz y foto para la misma clase.
003 cubre clases; 004 añade estados sin muestra/error; 005 completa la gestión de cuentas y archivo.
Políticas y límites de administración directa: [REGLAS_NEGOCIO.md](REGLAS_NEGOCIO.md).
Modelo, laboratorio y límites: [CLASES_Y_REVISION.md](CLASES_Y_REVISION.md).

## Fase 4 — Calidad y seguridad del reconocimiento

- [x] Un fallo de audio devuelve un resultado de error estructurado; nunca equivale a todos ausentes.
- [x] No marcar ausente automáticamente a quien no registró voz/rostro; exigir decisión manual con motivo.
- [x] Rechazar silencio, muestras demasiado cortas o sin actividad vocal suficiente y vectores no válidos antes de guardar.
- [x] Validar dimensiones y valores: rostro 128D sin reescalar; voz 256D normalizada antes de guardar/comparar.
- [x] Exigir un solo rostro completo al registrar/acceder, convertir a RGB y acotar formato, bytes y resolución.
- [ ] Evaluar iluminación, desenfoque, poses y calibrar límites con dispositivos reales, al final.
- [ ] Evaluar segmentación/diarización: las pausas de energía y el VAD actuales no separan hablantes solapados.
- [x] Sustituir SVM por comparación de referencias con cero, una y pocas identidades; errores de referencias visibles.
- [x] Rechazo por umbral y margen, empates y perfiles faciales ajenos a la matrícula; pruebas sintéticas de reconocimiento.
- [ ] Conjunto de evaluación consentido: falsos positivos, falsos negativos, ruido, iluminación y umbrales.
- [ ] Múltiples muestras por persona y actualización de biometría con autorización.
- [x] Invalidación específica del clasificador facial; el alta no vacía la caché global ni entrena después del COMMIT.
- [ ] Diseñar y evaluar presencia real/anti-reproducción para fotos y audios.
- [x] Alta docente con autorización privada, contraseña de 8–72 bytes UTF-8 y bloqueo de quince minutos tras cinco fallos.
- [x] Evaluador FAR/FRR/confusiones y propuesta de calibración sin aplicación automática; mediciones reales aplazadas.

Criterio de salida: no se presentan porcentajes de precisión sin mediciones y un error técnico no
produce una decisión académica automática.
Contrato, migración y límites de esta primera corrección: [ESTADOS_DETECCION.md](ESTADOS_DETECCION.md).
Validaciones del punto 3 y límites operativos: [VALIDACION_MUESTRAS.md](VALIDACION_MUESTRAS.md).
Comparador, parámetros y evaluación: [RECONOCIMIENTO.md](RECONOCIMIENTO.md).

## Fase 5 — Rendimiento, interfaz y mantenimiento

- [x] Rediseñar inicio, accesos, registro, paneles, tarjetas y diálogos con estilos compartidos y adaptación a móvil.
- [x] Ocultar la barra de desarrollo desde la configuración de arranque; no se detectó destello en Chrome/Brave con perfil nuevo, incluidas condiciones ralentizadas.
- [x] Cargar estilos antes de las pantallas e importar dlib/PyTorch/Resemblyzer únicamente al analizar capturas; prueba de imports en proceso nuevo.
- [x] Usar indicadores de progreso por operación y comprobar arranque y navegación con caché nueva, CPU x4 y latencia de 120 ms.
- [x] Sustituir consultas por materia con agregaciones en una sola consulta; comprobar conteos e indicadores de materias activas en Oracle.
- [ ] Medir consultas y recuperación con un volumen representativo durante el ensayo final.
- [ ] Registro de errores con contexto técnico sin contraseñas ni biometría; mensajes útiles en la interfaz.
- [x] Escapar texto dinámico de tarjetas y saludos antes de insertarlo en HTML; regresión con HTML malicioso.
- [x] Consolidar los estilos de la aplicación en static/css/styles.css y retirar reglas duplicadas, márgenes negativos y estilos antiguos.
- [x] Marca y pictogramas SVG locales, fuentes locales y prueba con solicitudes externas bloqueadas.
- [x] Revisar tema claro, móvil emulado, navegación con Tab, contraste de paleta y los dos estados del botón de contraseña.
- [x] Corregir el foco recortado de ambos campos de contraseña del registro docente; medidor local de fortaleza y coincidencia en vivo.
- [ ] Validar cámara/micrófono y móvil físico en el ensayo final; revisión completa de accesibilidad pendiente.
- [x] Retirada de biometría, archivo y respaldo cifrado con política inicial documentada en 005.
- [ ] Separar cuentas Oracle de ejecución y despliegue y acordar conservación institucional.
- [ ] Resolver licencia real y atribución: el README declara MIT, pero falta el archivo de licencia.
- [ ] Documentar inicio, parada, diagnóstico y recuperación. Mantener `source/` fuera de distribución.

## Fase 6 — Verificación antes de presentar

Por decisión del usuario, el ensayo real con dispositivos y el recorrido integral se harán al
final de las correcciones funcionales y visuales, como etapa de depuración y aceptación.
Las pruebas automáticas de cada cambio continúan durante el desarrollo.

- [ ] Pruebas unitarias de reglas relevantes y pruebas de integración con un esquema desechable separado.
- [x] Pruebas de paquetes y cinco disparadores: errores, rollback, cascadas, contexto y UPDATE sin cambios.
- [x] Regresión de sesiones y clases: editor manual, cambios de clase, dos conexiones simultáneas, reintentos y confirmaciones distintas.
- [ ] Flujo completo: profesor → materia → estudiante → matrícula → revisión → confirmación → reportes.
- [ ] Regresión específica para cada incidencia de estado, voz, imágenes y confirmación duplicada.
- [x] Restaurar respaldo y migrar 004→005 con historia sintética en cuentas temporales separadas, sin recrear la base activa.
- [ ] Instalación limpia en otro PC; cámara y micrófono reales; HTTPS local y acceso LAN.
- [ ] Automatizar las comprobaciones que no necesitan dispositivos ni credenciales privadas.

## Fase 7 — SQL Developer y presentación PL/SQL, al final

- [x] Preparar vistas sin hashes ni vectores para consulta y demostración.
- [x] Preparar `PKG_ASISTENCIA`: función de porcentaje y procedimientos de matrícula/asistencia.
- [x] Preparar consultas de demostración y exportación DDL mediante `DBMS_METADATA` desde SQL*Plus.
- [x] Documentar justificación individual, límites y alternativas de disparadores en [DISPARADORES_Y_PLSQL.md](DISPARADORES_Y_PLSQL.md).
- [x] Laboratorio SQL*Plus con procedimientos, función, cursor FOR, excepciones y rollback de fixtures.
- [x] Laboratorio 003: apertura de clase, revisión inicial, reintento idempotente y rechazo de otra propuesta, con rollback.
- [x] Laboratorio 004: análisis fallido no confirmable, sin muestra con resolución manual y conservación de NULL, con rollback.
- [ ] Conectar SQL Developer como `UPC_ASISTENCIA`, rol Default, servicio `XEPDB1`, al mismo Oracle.
- [ ] Importar el diccionario en Data Modeler y revisar tablas, PK, FK y cardinalidades.
- [ ] Guardar el diseño editable y exportar el diagrama para la presentación.
- [ ] Si se requieren vistas adicionales, utilizar Table to View Wizard y revisar el DDL generado.
- [ ] Separar visualización del diagrama y vistas SQL: el asistente de vistas no es necesario para dibujar relaciones.
- [ ] Presentar decisiones de modelo, restricciones, consultas, procedimientos, función y manejo de errores.

## Revisión actual: siete puntos y decisión del usuario

Estos números corresponden a la última lista de trabajo, no a los números de las fases anteriores.
Primero se completaron 1, 3 y 4. Después el usuario autorizó el frontend del punto 2.
Siguen pendientes 5, 6 y 7.

| Punto | Trabajo | Estado |
| --- | --- | --- |
| 1 | Clasificador con pocos estudiantes, desconocidos, matrícula y evaluación | Implementado y probado con datos sintéticos; medición real en punto 6 |
| 2 | Frontend, destello inicial, carga e importaciones | Implementado; medidor de claves y revisión de escritorio/móvil, incluido acceso administrativo real |
| 3 | Validaciones, cuentas, sesiones, duplicados, retiro, archivo y biometría | Implementado hasta 008, con administración, sesiones globales y excepciones; suite de 217 pruebas aprobada |
| 4 | Respaldo autenticado, restauración y actualización conservando historia | Implementado; ensayo real en dos esquemas temporales con datos sintéticos |
| 5 | Portabilidad, dependencias por plataforma, documentación general y licencia | Aplazado; las guías específicas de los cambios sí se actualizaron |
| 6 | Depuración integral, dispositivos reales, calibración y ensayo en otro PC/LAN | Aplazado hasta terminar correcciones funcionales y visuales |
| 7 | SQL Developer, Data Modeler y presentación visual | Aplazado para el final |

La migración de la aplicación conserva su esquema y sus datos. La recuperación se ensayó
con historia creada antes de 005, biometría sintética, Unicode, NULL, auditoría, revisión manual,
offset y continuidad de identidades. También se rechazaron clave incorrecta, copia alterada
y destino ocupado. Los usuarios temporales del ensayo se eliminaron; la cuenta activa no se
reemplazó. El detalle y las rutas de evidencia están en [CIERRE_1_3_4.md](CIERRE_1_3_4.md).

Quedan tareas de mayor alcance en las fases: calibración real, múltiples muestras, diarización,
prueba de presencia real, separación entre propietario y usuario de ejecución, políticas
institucionales de conservación y operación externa de respaldos. No se consideran demostradas
por las pruebas sintéticas ni por cerrar los tres puntos funcionales de esta revisión.
La instalación en otras plataformas y la recuperación con volumen grande siguen sin ensayarse.

Guías de esta entrega: [reglas de negocio](REGLAS_NEGOCIO.md),
[reconocimiento](RECONOCIMIENTO.md) y [recuperación](RECUPERACION.md).

## Referencias revisadas

- [Artículo mencionado: How to Create Views for All Tables with Oracle SQL Developer](https://www.thatjeffsmith.com/archive/2013/11/how-to-create-views-for-all-tables-with-oracle-sql-developer/).
- [Oracle Data Modeler: conceptos y uso](https://docs.oracle.com/en/database/oracle/sql-developer-data-modeler/22.2/dmdug/data-modeler-concepts-usage.html).
- [Configuración oficial de Streamlit, incluidos sslCertFile y sslKeyFile](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).
- [Configuración del intérprete de Python en VS Code](https://code.visualstudio.com/docs/python/settings-reference).

Streamlit documenta su TLS integrado para desarrollo; para una publicación productiva se planificará
terminación TLS mediante un proxy. Los menús del artículo de 2013 pueden cambiar según la edición de SQL Developer.

Evidencias y límites de esta primera implementación: [VALIDACION_INICIAL.md](VALIDACION_INICIAL.md).
