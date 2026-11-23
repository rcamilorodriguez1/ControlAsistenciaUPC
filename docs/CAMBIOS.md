# Registro de cambios de UPC | Aula

## 22/11/2026 — Memoria integral 1.2 actualizada a Oracle 009

- Se revisa el PDF 1.1 (76 páginas) y se genera la edición 1.2 (87 páginas), con Oracle
  009, Render, separación de cuentas, perfiles/agenda docente, configuración y excepciones
  de entrega manual. Créditos nominales completos y evidencia/aceptación diferenciadas.
- La guía funcional Oracle se actualiza y el diccionario vigente pasa al anexo B:
  las 14 tablas, 140 columnas y restricciones de Autonomous 009, sin repetir otra lista
  histórica de columnas. Se mantienen las consultas de estudio y la procedencia de cada evidencia.
- Se revisan tablas apaisadas, márgenes, índices numerados y metadatos. Resultado:
  104 enlaces, 168 marcadores, cobertura de las 140 columnas y cero texto fuera de página.
- Generación y revisión documental con archivos locales, sin Oracle ni prueba de la
  página/cámara. La contraseña común de pruebas y las demás claves permanecen privadas.
  Evidencia: .local/memoria_pdf/validacion.json y .local/presentacion/validacion_final.json.

## 22/11/2026 — Archivo privado de clave estudiantil para pruebas

- Se crea `.local/ALTA_ESTUDIANTE.md`, equivalente al de alta docente, con una clave
  compartida para autorizar las excepciones de los alumnos de prueba.
- El docente asigna esa clave al autorizar a cada alumno; el acceso sigue utilizando
  su propio documento, autorización vigente y contraseña registrada mediante hash.
- Se protege también el nombre `ALTA_ESTUDIANTE.md` en `.gitignore` y se documenta
  su uso sin incluir la clave. No se modifican cuentas ni credenciales existentes.
- Verificación técnica: formato de contraseña válido, clave distinta a la de alta
  docente, archivo ignorado por Git y ausencia de la clave en los archivos publicados.


## 22/11/2026 — Alcance de pruebas y alojamiento confirmado

- Instrucción expresa: el usuario realiza las pruebas de la página, cámara y
  reconocimiento; este PC no tiene cámara. Se detiene la revisión de la página y
  se termina la implementación/documentación con comprobaciones técnicas.
- Vercel queda descartado; solo Render aloja la aplicación para pruebas y presentación.
  Oracle Autonomous continúa como base de datos. Se retira la alternativa del roadmap
  activo; las menciones anteriores en el registro de cambios conservan su carácter histórico.
- Al terminar, registrar los cambios, realizar commit local y push, según lo solicitado.


## 22/11/2026 — Catálogo, diccionario, conexión y aporte académico

- La rama de base de datos entrega un catálogo HTML autónomo con búsqueda, selección
  de tabla y mapa de relaciones: 14 tablas, 140 columnas y 11 FK, desde Autonomous 009.
- El diccionario Markdown contiene tipos, nulabilidad, identidades, claves, valores
  predeterminados, reglas CHECK y significados. La semántica existente se conserva
  en una plantilla; los metadatos se vuelven a contrastar mediante el generador.
- Se documenta el recorrido navegador → Render → driver/pools → Oracle, TLS/ACL,
  sesiones y diferencias entre propietario, runtime y conexión administrativa limitada.
- Goodwill cubre valor por participante, beneficios esperados, indicadores para
  medirlos, aporte a Base de Datos y límites académicos, sin inventar precisión ni ahorros.
- Roadmap general e índice enlazan las dos ramas. El plan anterior y el diccionario
  001–008 se identifican como históricos; el PDF conserva su edición 1.1 sin regenerar.
- Verificación: extracción de metadatos sin filas de personas ni credenciales; búsqueda
  y selección probadas en Orca; presentación móvil a 390 px sin desbordamiento de página;
  enlaces locales y cobertura del diccionario revisados. Capturas y comprobaciones
  privadas en .local/revision_22nov. El catálogo funciona al abrir su index.html local.


## 22/11/2026 — Excepción docente con entrega manual y migración 009

- El portal docente añade Excepciones de acceso: materia propia, alumno matriculado,
  documento comprobado, clave confirmada, referencia y vigencia. La entrega es manual;
  se sustituye la propuesta de correo. El alumno usa su documento y clave en el acceso alternativo.
- El docente renueva/revoca sus autorizaciones; no sustituye las ajenas ni administrativas.
  Administración conserva la capacidad de revisar/sustituirlas. Los campos sensibles
  se limpian tras autorizar y no se pueden recuperar contraseñas desde Oracle.
- 009 añade dos FK/columnas a VERIFICACION_ESTUDIANTES y PKG_EXCEPCIONES_DOCENTES,
  con validación de contexto, propiedad, matrícula, versión y autoría. No añade tablas
  ni borra registros existentes. El runtime conserva 53 permisos y la cuenta técnica
  restringida pasa a cinco EXECUTE, sin DML directo de aprobación.
- Migración aplicada en Oracle local y Autonomous tras respaldos cifrados verificados.
  Inventario cloud: 14 tablas, 11 vistas, 10 triggers, 8 paquetes válidos; preflight con
  la cuenta runtime real aprobado. Preparadores e instaladores actualizados a 009.
- Verificación completa: 293 pruebas, 288 aprobadas y 5 omitidas (requieren un usuario
  Oracle temporal limitado). Incluye 7 de excepciones docentes, 3 de su interfaz,
  regresiones de acceso y pruebas reales Oracle con datos sintéticos y limpieza por ID.
  Evidencias privadas: .local/revision_22nov/pruebas.json y .local/oracle_cloud/migracion_009.json.
- Queda pendiente la aceptación funcional de estas pantallas con el usuario en Render.


## 22/11/2026 — Perfil y configuración del docente

- El menú de cuenta abre Mi perfil y Configuración para docentes. Ambas rutas exigen
  la sesión vigente; el repositorio contrasta el actor con el contexto Oracle.
- Perfil: identidad, materias propias activas/archivadas, calendario mensual, detalle
  de clases por día y próximas sesiones. No se inventan clases recurrentes ni asistencia.
- Archivo de materias y cuenta se traslada del portal docente a Configuración. Se
  conserva el historial; no se añade eliminación física de cuentas.
- Los portales priorizan operaciones y enlazan el perfil; el estudiante conserva su
  historial y porcentajes en su perfil. La agenda docente usa una estética propia.
- Verificación: 5 pruebas de perfil y 8 de navegación aprobadas; consulta compilada en
  Autonomous con ID inexistente, sin leer datos personales. Revisión Orca con datos
  sintéticos a 390 px sin desbordamiento horizontal; comprobación de escritorio.
- Falta la aceptación del usuario en Render y la autorización docente de excepciones.


## 22/11/2026 — Selector de clases independiente por docente y materia

- Se retira #ID de la etiqueta: el ID era global de Oracle, no un contador de clases
  pendientes por materia. Se conserva internamente para confirmar la clase correcta.
- La clave del selector incluye docente y materia; se descarta una selección que ya
  no esté en la lista autorizada. La consulta contrasta el docente con el contexto Oracle.
- No se elimina ninguna clase ni registro académico.
- Verificación: 2 pruebas de selección, cambio de docente/materia e ID ajeno aprobadas.


## 22/11/2026 — Roadmap general, créditos y encabezados

- Se conserva el plan anterior como ROADMAP_HISTORICO y se enlazan dos ramas:
  frontend/backend y base de datos/aporte académico. La arquitectura futura mantiene
  su rama. Goodwill se refiere a valor, beneficios y aporte académico.
- Se sustituyen los nombres provisionales del pie por Rafael Camilo Rodriguez Ayala,
  Harold Steven Torres Diaz, Oscar William Rivero Ordoñez y el docente Amilkat Sierra Romano.
- Se oculta el control de ancla de los títulos nativos; los enlaces de navegación
  y la semántica de los encabezados permanecen disponibles.
- La entrega manual de la clave sustituye la propuesta anterior de correo.
- Verificación: pruebas de frontend y revisión de enlaces documentales; la revisión
  visual con nombres largos se realiza junto al perfil docente.


Este archivo resume las entregas y enlaza su documentación. Para localizar todas las guías,
consultar el [índice](README.md); para trabajo pendiente, el [roadmap](ROADMAP.md).
Los resultados indicados corresponden a las verificaciones registradas en cada entrega.

## 22 de noviembre de 2026 — Reutilización del clasificador y audio por bloques

Se aplican dos mejoras acotadas para continuar usando Render tras las pruebas satisfactorias
comunicadas por el usuario: un clasificador de voz por grabación, reutilizado entre
intervenciones, y lectura WAV por bloques de hasta 65.536 muestras, conservando solo
la onda mono completa. No se modifican los modelos ni los criterios de reconocimiento.

Las pruebas específicas de voz/resultados y muestras validan varias intervenciones,
coincidencias conservadas, rechazos y equivalencia exacta de la onda frente a la lectura
anterior. También se comprobó dlib real con la lectura de una imagen sintética sin personas,
sin conexión Oracle. Regresión general: 276 pruebas ejecutadas, 207 aprobadas y 69
omitidas por integraciones no habilitadas; sin fallos. Evidencia privada:
`.local/hosting/pruebas_optimizacion.json` y su log. [Detalle](RECONOCIMIENTO.md#reutilización-y-lectura-de-audio).

Son los cambios menores cuarto y quinto desde 2c3baaf. Tras pasar las comprobaciones,
corresponde commit de estos dos pendientes y push de todo el lote, según la cadencia.

## 22 de noviembre de 2026 — Fotos comprimidas y miniaturas para reducir memoria

La sesión docente conserva los originales JPEG/PNG comprimidos y miniaturas, en lugar
de mantener todas las fotografías RGB descomprimidas. La galería utiliza las miniaturas;
la IA abre cada original a su resolución completa con la misma orientación y conversión
RGB. Se mantienen los límites de captura, los modelos, umbrales y validaciones de matrícula.

Pruebas: 22 de sesiones y 19 de interfaz aprobadas, con igualdad de píxeles, orientación
EXIF, liberación de imágenes y uso del original en el análisis. Una muestra JPEG sintética
de 2048 × 1536 reduce su almacenamiento de 9.437.184 a 2.428.600 bytes (74,27 %); no se
presenta como medida de memoria total en Render. [Detalle](RECONOCIMIENTO.md#uso-de-memoria-de-las-capturas-en-render).

Este es el tercer cambio menor desde 2c3baaf, tras el registro de requisitos y la revisión
de recursos. Corresponde commit local; el umbral de push aún no se alcanza.

## 22 de noviembre de 2026 — Prioridad de recursos para biometría

El usuario precisa que el límite relevante para la presentación es memoria/CPU del
reconocimiento facial y de voz. La revisión del código confirma carga diferida y caché
de modelos ya implementadas; no se presentan como mejoras nuevas ni como mediciones.
Quedan por medir RAM, CPU y latencia en el servicio con rostro y voz cargados, capturas
grandes y concurrencia. Los logs disponibles no demuestran todavía un fallo por memoria.

Se registra en el segundo roadmap que trasladar únicamente las pantallas a Vercel
mantendría la carga de inferencia donde se ejecute el backend. Se evaluará optimizar o
aislar el motor biométrico antes de decidir un rediseño de interfaz. No se cambia el
alojamiento, los modelos ni el código en esta revisión. Es el segundo cambio menor
documental desde el último push; no corresponde commit o push todavía.

## 22 de noviembre de 2026 — Requisitos de excepción docente, correo y alternativa Vercel

Se retoma por petición del usuario el apartado docente para autorizar acceso excepcional
y enviar la contraseña al correo del estudiante. Se acuerda recoger el correo en el registro
y permitir su gestión desde el perfil de alumnos existentes, guardándolo en Oracle. El
remitente institucional del usuario se plantea para pruebas y presentación académica,
sin carácter oficial; el proveedor y su configuración siguen pendientes.

Se registra la alternativa de interfaz en Vercel y backend en Render, además de evaluar
otros alojamientos frente a los límites de recursos. La aplicación actual usa Streamlit
en un proceso; separar interfaz y backend requiere adaptación y no se presenta como un
despliegue ya realizado. Tampoco se han cambiado aún contraseñas, permisos, esquema o
formularios, ni enviado correos. Se mantienen las funciones del servicio publicado.

Alcance y fuentes: [excepciones](EXCEPCIONES_BIOMETRICAS.md#requisito-retomado-autorización-docente-y-correo)
y [alternativa de alojamiento](ROADMAP_2.md#alternativa-de-alojamiento-vercel-y-render).
Esta actualización de requisitos cuenta como un cambio menor desde el último push,
pendiente de agruparse según la cadencia acordada.

## 22 de noviembre de 2026 — Render Live y punto 6 completado

Tras añadir los rangos `74.220.49.0/24` y `74.220.57.0/24` a la ACL de Autonomous,
conservando las entradas del PC, el usuario ejecuta un despliegue manual de `20ed6be`.
Render informa Deploy succeeded / Live. Los logs confirman «Configuración de producción
comprobada; Oracle y permisos comprobados» y el servidor en `0.0.0.0:8501`.

Comprobación independiente por HTTPS: `/_stcore/health` devuelve HTTP 200 y `ok`;
`/` devuelve HTTP 200 con el HTML de Streamlit. Evidencia privada:
`.local/render/despliegue_verificado.json`. No se ejecutan operaciones académicas ni
se considera que recibir el HTML valide los portales, cámara, voz o concurrencia.

Se cierra el punto 6 del primer roadmap: imagen Docker construida y ejecutada en Render.
El punto 5 conserva las cuentas web y la decisión sobre datos pendientes; el punto 7
conserva QR y persistencia; el ensayo integral y SQL Developer permanecen en el punto 8.
La instalación Oracle local y la clave de identidad original permanecen intactas.

Se agrupan tres cambios documentales: cadencia, diagnóstico de conexión y registro del
arranque correcto. Corresponde guardar el commit y hacer push por el cierre del punto 6,
según la autorización vigente, sin esperar cinco cambios. Esta publicación modifica MD;
el código del servicio que pasó los controles corresponde a `20ed6be`.

## 22 de noviembre de 2026 — Diagnóstico Oracle tras el arranque en Render

Los logs posteriores al push pasan las comprobaciones de URL y clave de identidad, pero
el arranque termina con OperationalError al comprobar Oracle. Streamlit todavía no se
inicia; los avisos «No open ports detected» son consecuencia de esa interrupción y no
acreditan por sí solos un fallo de puerto.

Se comprueban las credenciales cloud desde el PC mediante conexiones TLS y consultas de
solo lectura: UPC_AULA_APP sobre UPC_ASISTENCIA con 53 permisos, y UPC_ADMIN_APP con
acceso a las tres vistas administrativas. Evidencia privada:
`.local/oracle_cloud/render_diagnostico_pc.json`. No se cambian cuentas, claves ni datos.
Esto no acredita acceso desde Render ni que sus variables coincidan con el perfil del PC.

La captura de Connect > Outbound comunica `74.220.49.0/24` y `74.220.57.0/24`.
Continuación: revisar su autorización como bloques CIDR en Autonomous, conservando la
entrada del PC. La aplicación de la ACL y la conexión desde Render siguen pendientes;
la ACL es una hipótesis de red pendiente de comprobar.
El mensaje de OperationalError no incluye el código Oracle ni distingue su causa.
Esta unidad de diagnóstico y documentación es el segundo cambio menor desde 20ed6be;
no se crea otro commit o push todavía.

## 22 de noviembre de 2026 — Cadencia de commits y publicación

El usuario autoriza commit cada 3 cambios menores y push cada 5 cambios terminados o al
completar un punto del roadmap, lo que suceda primero. El agente clasifica el impacto;
los cambios mayores se guardan en commits propios. Se conserva MD → commit → push y
se documentan los criterios y contadores en el [índice](README.md#cadencia-de-commits-y-push).
Una unidad lógica cuenta una vez aunque incluya código, pruebas y documentación.

El último push verificado publicó `20ed6be` en `main`, incluido el ajuste de VS Code.
La captura más reciente de Render sigue esperando el control de salud en el puerto 10000;
ese aviso no identifica la causa ni confirma un arranque correcto. Revisar el commit y
los registros de la ejecución actual antes de diagnosticarlo o cerrar el despliegue.

Esta actualización documental cuenta como 1 cambio menor desde ese push y queda guardada
en los MD, pendiente de agruparse en el siguiente commit según la nueva cadencia.

## 22 de noviembre de 2026 — Configuración de variables en terminales de VS Code

Se incorpora el cambio pendiente de `.vscode/settings.json`: `python.terminal.useEnvFile=true`,
conservando el intérprete y la activación del entorno virtual existentes. Permite cargar
el `.env` configurado para las terminales Python; no incluye valores privados ni selecciona
el perfil `.local/render/.env` como configuración local. Se documenta en
[instalación](INSTALACION.md). Comprobaciones: JSON válido, cambio de configuración
revisado y exclusión de los archivos privados conservada.

El push anterior ya publicó aaad858, de3e471 y 2c6662f; se verificó que `main` de GitHub
apunta a 2c6662f. Todavía no se ha confirmado el resultado del nuevo despliegue en Render.
Este ajuste del editor se guarda en un commit local separado.

## 22 de noviembre de 2026 — Contexto de Render y orden de registro y publicación

Se conserva la organización documental existente: CAMBIOS.md para entregas y evidencias,
ROADMAP.md para estado y continuación, DESPLIEGUE.md para la configuración operativa,
y README.md como índice. Se registra el orden de trabajo acordado: **MD con los
cambios → commit local → push**. El contexto se mantiene en esos documentos del proyecto.

Se actualizan el roadmap y la portada del proyecto con Render como continuación de
alojamiento y Autonomous como base. El primer intento construyó b775e9a y se detuvo
al arrancar por APP_BASE_URL ausente; los registros posteriores avanzan a la validación
de la clave, incompatible con el lector binario de esa versión. URL asignada:
https://controlasistenciaupc.onrender.com; todavía no hay un servicio aceptado como operativo.

La separación Oracle está en el commit local aaad858 y la adaptación Base64 en de3e471,
con 12 pruebas de despliegue y 6 de identidad aprobadas. El perfil privado de Render
incluye la URL real y la copia Base64 conserva la clave original. Los secretos permanecen
en `.local/` y Render; no se incorporan al commit. Esta continuación guarda documentación
y commit local; el push y el ensayo de la versión actual quedan para el paso posterior.

## 22 de noviembre de 2026 — Preparación alternativa para Render

Se prepara la configuración privada para un Web Service Docker en Render, manteniendo
Oracle Autonomous como base. La clave de identidad original puede leerse desde un archivo
Base64 con `IDENTIDAD_CLAVE_FORMATO=base64`; se conserva el formato binario por defecto,
las huellas existentes y el rechazo de archivos inválidos o ausentes, sin generar otra clave.
Los archivos privados de importación permanecen fuera de Git y de la imagen.

Doce pruebas de despliegue y seis de verificación de identidad aprobadas, incluida
equivalencia de huellas entre formatos. El primer intento en Render construyó la imagen
de `b775e9a`; se detuvo al arrancar por configuración y por falta del lector Base64.
Publicación y construcción de la versión actual, conectividad y ensayo completo pendientes.
Configuración y límites: [despliegue](DESPLIEGUE.md#alternativa-preparada-render-y-oracle-autonomous).

## 22 de noviembre de 2026 — Cuenta de ejecución cloud verificada; punto 4 cerrado

El usuario completó el preparador y comunicó su resultado correcto. Se contrastó la
evidencia privada local: UPC_AULA_APP sobre el esquema UPC_ASISTENCIA, 53 permisos
verificados, 55 sentencias analizadas sin ejecutar sus operaciones, cero objetos propios
y verificado=true. Existe `.local/oracle_cloud/credenciales_ejecucion.toml`; ADMIN no se
guardó y la configuración local de Streamlit no cambió.

Se cierra el entregable 4 del primer roadmap y se actualizan las guías de ejecución,
despliegue, base de datos y administración. El punto 5 debe preparar la configuración
web cloud y la integración del perfil; VM, Docker real, dominio y ensayo público siguen
pendientes. No se repite el aprovisionamiento ni se presentan los portales como publicados.

## 22 de noviembre de 2026 — Diagnóstico de autenticación en preparación cloud

Tras el ORA-01017 comunicado, se comprueba que no existe el perfil de ejecución: en la
preparación normal el rechazo ocurre en el acceso de ADMIN, antes de generar credenciales
o crear usuarios. El preparador identifica ahora la fase de autenticación/creación/permisos
y ofrece un mensaje específico para ADMIN, conservando claves y sin reintentos automáticos.
No se intenta iniciar sesión como ADMIN desde el agente ni se restablecen contraseñas.

**Verificación:** 16 pruebas de cuenta de ejecución aprobadas, incluidas dos nuevas que
comprueban el diagnóstico, ausencia de credenciales en mensajes, conservación de archivos
y rechazo antes de conceder permisos. La activación definitiva sigue pendiente.

## 21 de noviembre de 2026 — Cuenta de ejecución preparada y ensayada

Se implementa `ORACLE_ESQUEMA` separado de `ORACLE_USUARIO`, con callback del pool y
restauración del esquema al adquirir conexiones. La administración resuelve el propietario
explícito. Las comprobaciones de producción/HMAC consultan metadatos por propietario;
respaldo y restauración rechazan conexiones runtime antes de operar sobre un esquema vacío.

Los scripts cloud 06–08 preparan `UPC_AULA_APP` con CREATE SESSION y un contrato de
28 GRANT, equivalente a 17 permisos de objeto y 36 de columna. No recibe roles, cuota,
objetos propios, DDL, GRANT OPTION ni los paquetes administrativos. El preflight comprueba
el contrato exacto. El alta web administrativa exige el propietario; su herramienta acepta
un perfil privado explícito con `--config-oracle`. La plantilla productiva usa el runtime,
sin guardar la contraseña propietaria en el contenedor normal.

`scripts/preparar_ejecucion_cloud.py` solicita ADMIN sin eco ni almacenamiento, conserva
la clave nueva antes del DDL, rechaza cuentas existentes y ofrece plan offline, verificación
y continuación autenticada sin cambiar claves. No modifica los secretos ni Oracle local.
La creación definitiva cloud todavía requiere ejecutar el preparador en la terminal.

**Verificación:** regresión completa con Oracle habilitado: 265 pruebas, 260 aprobadas y
cinco del perfil temporal omitidas en esa ejecución. Las cinco se ejecutaron por separado
y pasaron con un usuario XE temporal limitado: catálogo, permisos y denegaciones, clase,
matrícula, sesiones, perfil, preflight y reutilización del pool. Sus filas se revirtieron y
la cuenta sin objetos se retiró sin CASCADE. Una consulta TLS de solo lectura confirmó que
UPC_AULA_APP todavía no existe en Autonomous; nueve consultas nuevas de metadatos se
analizaron correctamente allí. No se presenta el punto 4 como cerrado en cloud.

Guía: [CUENTA_EJECUCION.md](CUENTA_EJECUCION.md). Evidencias privadas:
`.local/ejecucion/pruebas_completas.log`, `pruebas_oracle.log` y `cloud_preparacion.json`.
No se cambian tablas, disparadores ni paquetes de negocio ni se inicia el segundo roadmap.

## 21 de noviembre de 2026 — Preparación de red OCI confirmada en consola

El usuario creó `upc-aula-igw` y confirmó la ruta `0.0.0.0/0` hacia esa puerta en la tabla
de la subred pública. Las capturas muestran la puerta Available y reglas de entrada
con estado: SSH TCP 22 desde la IP administrativa `/32`, HTTP 80 y HTTPS 443 públicos;
se conservan las reglas ICMP y la salida general. La IP administrativa real no se copia
a esta documentación. El usuario volvió a recibir falta de capacidad en los tres AD.

Se actualizan roadmap y guía de despliegue. La configuración de red está preparada según
las evidencias de consola; habilitación, asociación de ruta y conectividad efectiva
permanecen pendientes de ensayo con la VM. No se modifican la aplicación ni Oracle.
El PDF 1.1 conserva el corte anterior a esta preparación, conforme a su carácter de edición.

## 21 de noviembre de 2026 — Memoria integral actualizada a edición 1.1

Se revisa la edición del 18/11 y se actualizan la memoria principal, la guía de base de
datos, el HTML y el PDF. La nueva edición tiene 76 páginas e incorpora catálogo SQL,
instalación Autonomous 001–008, recuperación de ORA-20021, preparación Docker/Caddy,
verificaciones entre navegadores y los dos roadmaps. Conserva la procedencia local del
diccionario del 18/11 y distingue esa consulta de las comprobaciones cloud posteriores.
Registra la falta de capacidad A1.Flex en los tres AD; no declara la aplicación publicada.

Se incorpora `scripts/generar_documentacion.py` para regenerar desde las fuentes actuales,
con detección de navegador y perfil temporal. Sus dependencias opcionales quedan en
`docs/requirements-documentacion.txt`, separadas de las del portal. El índice de guías
explica el procedimiento. Se conservó una copia privada de la edición anterior.

**Verificación documental:** 2.375 unidades de contenido encontradas en el PDF, 29 entradas
de índice con destino correcto, 171 marcadores y 87 enlaces. Sin texto fuera de márgenes,
contenido omitido, rutas absolutas privadas ni coincidencias con las credenciales locales
y cloud comprobadas en memoria. Inspección visual de las 76 páginas mediante hojas de
contacto; tablas del diccionario y restricciones conservadas en A4 apaisado.

Evidencia privada: `.local/memoria_pdf/validacion.json` y `revision_contenido.json`.
Los resultados funcionales citados son evidencias de entregas previas; no se ejecutaron
migraciones, pruebas de negocio ni cambios de la interfaz al actualizar la documentación.

## 21 de noviembre de 2026 — Estado de Compute y continuación sin VM

Se documentan la VCN y subred pública creadas y la confirmación del usuario de falta de
capacidad A1.Flex en AD-1, AD-2 y AD-3 de Ashburn. La VM no está creada; red, IP y acceso
SSH no se consideran verificados. El primer roadmap ordena trabajo que puede avanzar
sin servidor: completar red, separar la cuenta de ejecución, preparar configuración
cloud, validar Docker en Linux disponible y preparar recuperación/SQL Developer.

Solo cambia la documentación. No se cambian cuentas, credenciales, Oracle, la aplicación
ni recursos cloud; no se ejecuta el workflow ni se inicia el segundo roadmap.

## 21 de noviembre de 2026 — Organización de consultas y separación de roadmaps

El usuario confirma que solo tiene la base Autonomous, todavía sin VM Compute, y retoma
Docker para ejecutar la aplicación. El primer roadmap queda enfocado en organizar y
desplegar la versión actual; el [segundo roadmap](ROADMAP_2.md) registra las mejoras de
frontend, paquetes, disparadores, tablas, vistas y el traslado posterior de reglas a Oracle.

Se extraen 104 apariciones de SQL de nueve módulos a `sql/consultas/`, conservando sus
cadenas, parámetros y transacciones. Las sentencias idénticas se agrupan en `compartidas/`:
88 consultas únicas más dos plantillas de identificadores. El lector común valida rutas,
mantiene caché y restringe las plantillas a nombres Oracle. La generación técnica de DDL
de respaldos conserva su validación y queda identificada para la revisión posterior.

Este cambio no traslada reglas de negocio a nuevos paquetes, no altera tablas ni vistas
y no cambia el frontend. La conexión local sigue separada de cloud. Se actualizan la guía
de despliegue, el índice y los dos roadmaps al uso vigente de Docker.

**Verificación:** 182 pruebas aprobadas y 64 de integración omitidas; incluye cinco pruebas
del catálogo. Las 104 cadenas extraídas coinciden con su origen y se conserva el AST de
control/transacciones en la extracción. Se analizaron 65 consultas de lectura en Oracle
Cloud sin ejecución, todas correctas. La imagen Docker aún no está construida en Linux;
la VM, configuración de producción, permisos restantes y ensayo público siguen pendientes.

Evidencias privadas: `.local/reorganizacion/extraccion_sql.json`, `pruebas.log` y
`catalogo_cloud.json`. Guía del catálogo: [sql/consultas/README.md](../sql/consultas/README.md).

## 21 de noviembre de 2026 — Recuperación de ORA-20021 e instalación cloud completada

La primera ejecución se detuvo durante 002: `V_MATERIA_ESTUDIANTES` y
`V_REGISTROS_ASISTENCIA` quedaron INVALID después de modificar tablas; USER_ERRORS no
contenía errores de compilación. Se centraliza la recompilación del propio esquema en
`sql/36_recompilar_esquema.sql` y se incorpora antes de verificar las migraciones 002–008.
Se conserva el rechazo de objetos inválidos; no se relaja `04_verificar.sql`.

El instalador añade `--continuar`: valida destino, cuentas, estado y versiones consecutivas,
aplica solo migraciones pendientes y recupera los permisos si esa etapa quedó incompleta.
No recrea usuarios ni vuelve a ejecutar las tablas de 001. El plan inicial actualizado
tiene 229 sentencias. El diagnóstico utiliza consultas externas de objetos, errores y versiones.

**Verificación real:** continuadas 002–008 en la base Autonomous del proyecto usando las
claves técnicas originales. Instalación y permisos correctos; inventario: 14 tablas,
11 vistas, 10 disparadores, 7 paquetes y 7 cuerpos válidos. Estado privado `completada`.
Doce pruebas del instalador aprobadas, incluidas recuperación y rechazo de otro destino.
No se cambió Oracle local ni la conexión de la aplicación.

Evidencias privadas: `.local/oracle_cloud/diagnostico_ora20021.json`, `continuacion.log`
y `instalacion.json`. La reorganización del acceso SQL/PLSQL y la instalación del backend
sin Docker siguen pendientes.

## 21 de noviembre de 2026 — Instalador de usuarios y esquema cloud preparado

El usuario confirma la conexión TLS como ADMIN y una consulta de solo lectura correcta;
el resultado privado registra Oracle `23.26.4.1.0`. Se prepara
`scripts/preparar_oracle_cloud.py` para crear las dos cuentas técnicas, instalar las
versiones 001–008 y verificar objetos y permisos en Autonomous. No cambia el acceso local.

El SQL permanece en archivos externos. `_scripts_sql.py` expande `@`/`@@`, conserva bloques
PL/SQL terminados por `/` y rechaza comandos no soportados, ciclos y rutas externas.
El plan actual tiene 224 sentencias de instalación procedentes de 38 archivos fuente.
Las claves técnicas se guardan en un TOML privado antes del DDL; ADMIN se pide sin eco
y no se guarda. Una preparación existente no se sobrescribe ni se reinicia automáticamente.

Se añaden aprovisionamiento parametrizado, consultas de inventario y verificadores de
14 tablas, 11 vistas, 10 disparadores, 7 paquetes y los permisos de `UPC_ADMIN_APP`.
Siete pruebas nuevas cubren lectura de scripts, controles de repetición y conservación
de credenciales ante un fallo parcial. La suite completa considera 236 pruebas:
172 aprobadas y 64 de integración Oracle omitidas, sin cargar secretos locales.
La instalación real queda pendiente de ejecutar
el comando interactivo, que necesita la contraseña ADMIN en la terminal.
Procedimiento: [instalación cloud](INSTALACION.md#instalar-el-esquema-en-una-autonomous-nueva).

## 21 de noviembre de 2026 — Primera conexión a Autonomous y plan sin Docker

El usuario crea Autonomous `UPCAULA` en Ashburn, Always Free, 26ai, y confirma estado
Available. Selecciona una lista de IPs permitidas y conexión TLS sin exigir mTLS. Se registra
la decisión de instalar posteriormente el backend en una VM con Python y venv, sin Docker.
El procedimiento anterior de contenedores queda identificado como una referencia descartada.

Se guarda el descriptor aportado en `.local/oracle_cloud/dsn.txt`, eliminando una barra
invertida antes de `.adb`. No contiene contraseña y no entra en Git. Se añade
`scripts/probar_oracle_cloud.py`, que valida TCPS/verificación de servidor, limita reintentos,
permite comprobar red sin credenciales y solicita la contraseña sin eco para el acceso real.
La consulta está en `sql/cloud/02_comprobar_conexion.sql`, separada de Python. Solo consulta
usuario/base/servicio; no crea usuarios, objetos ni cambia el acceso Oracle local.

**Validación:** descriptor válido, DNS y puerto 1522 accesibles desde el PC y tres pruebas
unitarias correctas. **Pendiente:** autenticar como ADMIN y comprobar la consulta real.
La accesibilidad del puerto no se presenta como una conexión TLS/Oracle autenticada.
Instrucciones: [instalación](INSTALACION.md#primera-comprobación-de-oracle-cloud-desde-windows).

## 21 de noviembre de 2026 — Preparación para alojamiento en la nube

Se añaden Dockerfile de dos etapas, Compose con Caddy y plantillas privadas para una
instancia Linux con Oracle Autonomous Database. La aplicación se ejecuta sin root, el
proxy publica HTTPS y el estado privado persiste fuera de la imagen. El arranque local
Windows y el frontend conservan su configuración.

Los dos pools comparten transporte Oracle TLS/mTLS, con verificación del servidor y
rechazo de direcciones TCP en modo cloud. La configuración admite secretos por archivo
`KEY_FILE`. El nuevo arranque comprueba dominio, credenciales, clave de identidad,
versiones del esquema, objetos y permisos mediante consultas; no crea claves ni migra
la base. Se preparan SQL para crear cuentas en una Autonomous nueva y una herramienta
explícita de alta inicial administrativa, con contraseña sin eco y registro de auditoría.

Se incluye un flujo manual de GitHub Actions para construir y comprobar Linux x64/ARM64,
sin publicación ni despliegue. Guía y procedimientos: [DESPLIEGUE.md](DESPLIEGUE.md).

**Validación local:** suite de 226 pruebas, 162 aprobadas y 64 de integración Oracle
omitidas; incluye nueve pruebas nuevas. La suite también pasa sin cargar los secretos
locales. Carga de modelos facial/voz en CPU y `pip check` correctos. Compose TLS y mTLS
validados con la CLI oficial; preflight de configuración y servidor HTTP de prueba
correctos, con respuestas 200. No se modificó la base local.

**Pendiente:** construir/ejecutar el contenedor en Linux, ensayar los SQL y la conexión
en Autonomous, preparar infraestructura y dominio, trasladar los datos y sus claves si
corresponde y validar el recorrido público. Docker no está instalado en este PC; no se
presenta la imagen ni el flujo de GitHub como ejecutados. El punto 5 del roadmap sigue abierto.

## 21 de noviembre de 2026 — Revisión de Firefox y Edge

Se añade `scripts/verificar_firefox.py`, que automatiza el Firefox instalado mediante
WebDriver BiDi y perfiles temporales, reutilizando las mediciones y criterios extraídos a
`scripts/_frontend_mediciones.py`. El verificador de Chromium sigue utilizando los mismos
criterios. Se ajusta la detección de recortes de texto inline y la serialización de alineación
del menú para evitar falsos positivos entre motores.

Se corrige un desborde del pie en Firefox: `static/js/diseno.js` mide el ancho útil de `stMain`
con `ResizeObserver`, y el CSS lo utiliza para el ancho y centrado del pie. El encabezado
compartido carga el observador junto al complemento de foco existente. No se modifica el
separador aprobado, la identidad, las rutas, las sesiones ni la base de datos.

**Validación final:** 173 vistas correctas: Firefox 67, Edge 73, Chrome 21 y Brave 12.
Incluye tamaños de 1440/768/390/320 px según el recorrido, iconos, ambos estados de contraseña,
menús, materias, perfil, calendario y administración. Se reproduce también el fallo de la
fuente nativa. Diez pruebas existentes de frontend y navegación aprobadas. La instancia HTTPS
se reinicia con el código actual; los escenarios autenticados son sintéticos y tienen Oracle
bloqueado. La comprobación visual de foco de Firefox en dos formularios queda explícitamente
omitida porque la ventana automatizada no está activa; no se presenta como validada.

Archivos, límites y evidencias: [FRONTEND.md](FRONTEND.md#firefox-y-edge-revisión-entre-navegadores-21112026).

## 21 de noviembre de 2026 — Compatibilidad de iconos en Chrome

Se reproduce el defecto de nombres como `visibility` y `passkey` al bloquear la fuente
Material nativa. Se reutiliza el WOFF2 de Streamlit mediante una familia local y una URL
con huella de contenido, aislando sus ligaduras de la tipografía de texto. La corrección
se aplica a los tres roles, los menús y los dos estados de mostrar/ocultar contraseña.
No se añaden dependencias, fuentes remotas ni copias de la fuente al proyecto.

El verificador ahora comprueba que la fuente esté cargada y que el glifo se dibuje con ancho
de icono; añade el escenario `--fallo-fuente-iconos` y registra el motor del navegador.
Antes solo comprobaba el nombre de familia CSS, insuficiente para detectar esta condición.

**Validación:** 134 vistas correctas en Chrome y Brave, incluidas vistas móviles, menús,
perfil, administración y la instancia HTTPS real: 123 con fallo de fuente nativa simulado
y 11 en Chrome con las condiciones normales. Dos pruebas de frontend y ocho de
navegación aprobadas. Los recorridos autenticados son sintéticos y tienen Oracle bloqueado.
El usuario confirma «salen mejor» y aporta capturas de Chrome con el ojo, los iconos de los
botones del acceso docente y la casa de Inicio correctamente dibujados. Se registra esa mejora
visual; los demás recorridos conservan su estado de aceptación, incluido el separador aprobado.

Detalle y evidencias: [FRONTEND.md](FRONTEND.md#chrome-nombres-de-iconos-en-lugar-de-símbolos-21112026).

## 18 de noviembre de 2026 — Mockup navegable de pantallas

Se añade [docs/mockup/index.html](mockup/index.html), un mockup documental retrospectivo
de UPC | Aula con 18 pantallas o estados y 59 capturas originales. Reúne portada, accesos,
registro/recuperación docente, materias, revisión, registros, portal y perfil estudiantil,
verificación excepcional y acceso/consola administrativa. Incluye 13 variantes móviles,
búsqueda, Anterior/Siguiente y 39 enlaces de recorrido. Funciona desde el archivo HTML.

Las capturas proceden de revisiones anteriores correctas, anónimas o con datos sintéticos;
su procedencia, limitaciones y huellas se conservan en
[pantallas.json](mockup/pantallas.json) y en la [guía del mockup](mockup/README.md).
El logotipo es una copia binaria del original institucional. Los archivos de imagen no se editan.
La interfaz de referencia y la aceptación existente permanecen registradas por separado.

**Validación del visor:** 59 imágenes decodificadas, integridad de recursos y revisión de las
18 pantallas en 1440, 768, 390 y 320 px: 72 vistas sin desbordamiento horizontal. Comprobados
los 39 destinos de recorrido, búsqueda con/sin tildes, variantes inexistentes, controles de
dispositivo y navegación por teclado, incluido el salto al contenido conservando la pantalla.
Sin coincidencias con las credenciales locales en los archivos de texto compartidos.
Evidencias: `.local/mockup/validacion.json` y capturas del visor.

No se inicia la aplicación, no se conecta a Oracle y no se cambian autenticación, sesiones,
formularios o lógica de negocio. Este catálogo no sustituye el ensayo funcional pendiente.

## 18 de noviembre de 2026 — Memoria integral en PDF

Se prepara [UPC_Aula_Documentacion_Integral.pdf](UPC_Aula_Documentacion_Integral.pdf),
edición 1.0, con 72 páginas de documentación académica y técnica. Incluye planteamiento,
justificación, objetivos, alcance, requisitos, arquitectura, flujos por rol, seguridad,
identidad visual, operación, evidencias, pendientes y la guía completa de Oracle como anexo.
Se conservan fuentes editables en [INFORME_PROYECTO.md](INFORME_PROYECTO.md),
[BASE_DE_DATOS.md](BASE_DE_DATOS.md) y [HTML maquetado](UPC_Aula_Documentacion_Integral.html).

La plantilla A4 utiliza el logotipo original del manual UPC, verde institucional, índice
numerado con enlaces, 165 marcadores, diagramas y páginas apaisadas para tablas extensas.
La captura incluida pertenece a la aplicación actual. No se inventan nombres del equipo,
mediciones biométricas ni aprobaciones pendientes.

**Verificación:** inspección de las 72 páginas para detectar texto fuera de márgenes,
comprobación de integridad de 2.284 unidades de contenido, enlaces de navegación y revisión
visual de portada, índices, diagramas y tablas. Sin caracteres de reemplazo, credenciales
locales ni rutas personales detectadas. La generación no modifica código de aplicación,
dependencias de ejecución, datos ni objetos de Oracle.

## 18 de noviembre de 2026 — Guía de funcionamiento de la base de datos

Se añade [BASE_DE_DATOS.md](BASE_DE_DATOS.md), contrastada con el diccionario Oracle en modo de
solo lectura: 14 tablas, 138 columnas, 9 relaciones por FK, 11 vistas, 7 paquetes y 10 disparadores.
Incluye los flujos de aplicación, un catálogo de consultas de estudio, restricciones e índices,
y las vías de visualización en SQL Developer. Se prepara localmente `exports/modelo_008.sql`
con estructura, sin filas de usuarios y sin ejecutar sus sentencias DDL. La revisión no cambia
datos, objetos ni permisos de la base.

## 17 de noviembre de 2026 — README de UPC | Aula

Se sustituye la presentación heredada por un README en español centrado en UPC | Aula,
con el logotipo institucional y una captura de su portada. Se reorganizan las funciones por
rol, la tecnología, la puesta en marcha, las versiones de Oracle, la estructura, las pruebas
y los pendientes, enlazando las guías del proyecto. Los medios y la presentación del proyecto
de referencia dejan de utilizarse en el README.

## 17 de noviembre de 2026 — Versión local para ControlAsistenciaUPC

Se vincula el proyecto con [rcamilorodriguez1/ControlAsistenciaUPC](https://github.com/rcamilorodriguez1/ControlAsistenciaUPC),
rama `main`, usando la cuenta `HTrres-22`. Por instrucción del usuario, el contenido publicable
de esta carpeta local es la versión definitiva: incluye código, recursos institucionales,
dependencias, scripts SQL/PLSQL, pruebas y documentación; los archivos antiguos que solo estaban
en el remoto se retiran de la versión actual.

Se amplían las exclusiones de Git para mantener locales los entornos virtuales, cachés,
configuraciones privadas, credenciales, claves, certificados, datos biométricos, exportaciones,
respaldos y archivos de herramientas personales. Los ejemplos de configuración sí se incluyen.

**Validación:** revisión de los archivos exactos preparados contra las credenciales locales,
sin coincidencias detectadas; 217 pruebas aprobadas con Oracle habilitado sobre una copia de
los archivos publicables. El entorno y la configuración privada se proporcionaron únicamente
para ejecutar las pruebas y permanecen fuera del contenido versionado.

## 17 de noviembre de 2026 — Excepciones biométricas, esquema 008

**Motivo:** permitir el acceso de estudiantes que no pueden completar la verificación biométrica
por razones físicas, médicas, técnicas o administrativas, conservando control y trazabilidad.

Cambios implementados:

- Acceso alternativo con documento y contraseña, condicionado a autorización administrativa vigente.
- Alta administrativa de estudiantes sin muestras biométricas; autorización, renovación y revocación.
- Estado persistente de verificación pendiente, biométrica completa o excepcional, visible en el
  portal, perfil y consola administrativa, con consulta, filtros y exportación.
- Auditoría de autorizaciones, credenciales comprobadas, accesos y fallos; límite de intentos.
- Comprobación de autorización y credencial junto con la apertura de sesión; revocación y vencimiento
  validados en servidor. Se conservan los permisos y flujos de los demás roles.
- Migración 008, paquete `PKG_EXCEPCIONES`, verificador, permisos, instalación y diagnóstico actualizados.
- Corrección del cargador de restauración para evitar reutilizar parámetros tipados entre tablas vacías.

La política biométrica de acceso existente comprueba el rostro (un factor). La voz sigue en el
flujo de asistencia. La excepción no registra asistencia automáticamente.

**Validación registrada:** 217 pruebas aprobadas con Oracle habilitado; verificación SQL*Plus;
12 vistas de las pantallas nuevas en escritorio/tableta/móvil; 12 vistas anónimas de la instancia
HTTPS existente; restauración completa de 008 en esquemas temporales, incluidos estados de excepción.

**Pendiente:** aceptación del usuario y ensayo con personas y procedimientos institucionales reales.
El login institucional general del estudiante sigue siendo un trabajo separado.

**Detalle, archivos modificados y evidencias:** [EXCEPCIONES_BIOMETRICAS.md](EXCEPCIONES_BIOMETRICAS.md).
La guía también explica la conservación de la clave privada de identidad al trasladar o restaurar la base.

## 17 de noviembre de 2026 — Mi perfil del estudiante

Vista privada con porcentaje general de asistencia, número de materias matriculadas, resumen
de asistencias/ausencias, detalle por materia y calendario mensual. Utiliza los registros académicos
existentes y mantiene el control de acceso por rol.

**Estado:** implementado y probado; pendiente de confirmación visual del usuario.
**Detalle:** [PERFIL_ESTUDIANTE.md](PERFIL_ESTUDIANTE.md).

## Entregas anteriores

El detalle de las entregas anteriores se conserva en sus guías, incluidos sus resultados históricos:

| Entrega o área | Documentación |
| --- | --- |
| Identidad UPC \| Aula, tipografía, recursos institucionales y composición | [Identidad visual](IDENTIDAD_VISUAL.md) |
| Controles, encabezado, menú, separador de Cerrar sesión y aceptación visual | [Frontend](FRONTEND.md) |
| Pie académico compartido y zoom | [Pie académico](PIE_ACADEMICO.md), [zoom](ZOOM.md) |
| Recuperación de contraseña docente | [Recuperación de acceso](RECUPERACION_ACCESO.md) |
| Sesiones globales, navegación y esquema 007 | [Portal y sesiones](PORTAL_Y_SESIONES.md) |
| Rol administrativo y esquema 006 | [Administración](ADMINISTRACION.md) |
| Cuentas, matrícula, archivo y esquema 005 | [Reglas de negocio](REGLAS_NEGOCIO.md) |
| Estados de detección y esquema 004 | [Estados de detección](ESTADOS_DETECCION.md) |
| Clases y revisión manual, esquema 003 | [Clases y revisión](CLASES_Y_REVISION.md) |
| Disparadores y auditoría, esquema 002 | [Disparadores y PL/SQL](DISPARADORES_Y_PLSQL.md) |
| Entorno, HTTPS, respaldo y reconocimiento | [Instalación](INSTALACION.md), [recuperación](RECUPERACION.md), [reconocimiento](RECONOCIMIENTO.md) |
