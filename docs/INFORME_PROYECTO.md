# Documentación integral del proyecto UPC | Aula

Edición documental 1.2 · 22 de noviembre de 2026 · Esquema Oracle 001–009.

Autores: Rafael Camilo Rodriguez Ayala, Harold Steven Torres Diaz y Oscar William Rivero Ordoñez.
Docente de referencia académica: Amilkat Sierra Romano. Ingeniería de Sistemas · Base de Datos.

## 1. Resumen ejecutivo

**UPC | Aula** es un proyecto académico para el registro, la administración y el seguimiento
de la actividad de clase en el contexto de la Universidad Popular del Cesar. Organiza
asignaturas y grupos, matrículas, sesiones académicas, resultados de asistencia e historial.
Su interfaz reúne los portales docente, estudiantil y administrativo.

La aplicación está desarrollada en Python y Streamlit. Oracle conserva los datos y aplica
reglas mediante restricciones, paquetes PL/SQL y disparadores. El reconocimiento facial y
de voz produce propuestas que deben distinguirse de la decisión académica final. El diseño
mantiene un flujo de revisión docente y una alternativa autorizada para estudiantes que no
pueden completar la biometría.

Esta memoria documenta lo implementado, las decisiones de diseño, las verificaciones registradas
y el trabajo pendiente. Su propósito es facilitar comprensión, mantenimiento, pruebas y
presentación académica. Es documentación del proyecto; no constituye un acta de aprobación
institucional, una medición de precisión biométrica ni una declaración de despliegue productivo.

### 1.1 Estado de referencia

| Aspecto | Situación al corte documental del 22/11/2026 |
| --- | --- |
| Identidad | UPC Aula; logosímbolo original del manual UPC de 2010, Arial, verde institucional y lema Educación y Futuro. |
| Aplicación | Python 3.11 y Streamlit; portales docente, estudiantil y administrativo. |
| Alojamiento elegido | Render con Docker para toda la aplicación; Vercel descartado por el usuario. |
| Base | Oracle local XE y Autonomous UPCAula con versiones 001–009 verificadas; datos de cada entorno separados. |
| Persistencia | 14 tablas, 140 columnas visibles, 11 FK, 11 vistas, 10 triggers y 8 paquetes PL/SQL válidos. |
| Acceso Oracle | Propietario UPC_ASISTENCIA, runtime UPC_AULA_APP con 53 permisos y cuenta técnica UPC_ADMIN_APP con cinco EXECUTE. |
| Perfiles | Perfil estudiantil de asistencia y perfil docente de materias/agenda; configuración docente separada del portal. |
| Excepción de acceso | Autorización docente para alumnos matriculados y autorización administrativa; entrega manual de clave, con vigencia y revocación. |
| Pruebas técnicas | 293 pruebas ejecutadas: 288 aprobadas y 5 omitidas por requerir un usuario Oracle temporal limitado. |
| Despliegue comprobado | Evidencia Live de 20ed6be; commits posteriores publicados en main. El último despliegue y sus pantallas los verifica el usuario. |
| Aceptación pendiente | Pruebas de la página, cámara, voz y reconocimiento a cargo del usuario. Este PC no tiene cámara. |

### 1.2 Lectura y procedencia

La memoria distingue implementación, verificación técnica y aceptación del usuario.
El anexo A explica tablas, reglas, paquetes y consultas; el anexo B incorpora el
diccionario vigente obtenido de Autonomous 009: 140 columnas y sus restricciones.
Los enlaces permiten consultar las guías editables y el catálogo interactivo.

El inventario de columnas y FK procede del catálogo del 22/11. La verificación del
esquema y de los permisos se conserva en evidencias privadas; esta edición utiliza
esas evidencias y no ejecuta otra migración ni nuevas pruebas de la página. Las
capturas históricas, cuando se incluyen, están identificadas como tales.

## 2. Planteamiento del programa

### 2.1 Contexto y necesidad

El seguimiento de clases necesita vincular personas, asignaturas, grupos y sesiones concretas.
Una marca aislada de presencia no explica a qué clase corresponde, cómo se obtuvo, quién la
revisó ni qué pasó si luego se corrigió. El proyecto se plantea para reunir esa información
en un sistema que permita consultar tanto el estado actual como su historia.

La necesidad funcional incluye tres perspectivas: el docente requiere preparar y revisar la
asistencia; el estudiante necesita consultar sus materias y su participación; la administración
debe gestionar cuentas y revisar la trazabilidad. Los errores técnicos o las limitaciones para
usar biometría requieren un tratamiento explícito, distinto de declarar una ausencia.

Este planteamiento procede de los requisitos y revisiones del proyecto. No se presenta como
resultado de una encuesta, diagnóstico estadístico o estudio de procesos oficiales de la UPC.

### 2.2 Formulación del problema

¿Cómo integrar el registro y seguimiento de la actividad académica por asignatura, grupo y
sesión, con identificación de usuarios, revisión de resultados y trazabilidad, de modo que
los errores de reconocimiento o la imposibilidad de aportar biometría no se confundan con
decisiones académicas automáticas?

### 2.3 Problemas de diseño que se deben resolver

- Relacionar cada resultado con una sesión de clase inequívoca y su matrícula.
- Evitar duplicados por reintentos, varias pestañas o confirmaciones concurrentes.
- Distinguir una coincidencia, una falta de muestra y un fallo de análisis.
- Conservar responsables, motivos y valores anteriores cuando se corrige información.
- Separar acceso al sistema, verificación de identidad y registro de asistencia.
- Proteger credenciales y plantillas, manteniendo una alternativa de acceso autorizada.
- Preparar una instalación reproducible y una base comprensible para la presentación PL/SQL.

### 2.4 Justificación

**Académica.** El proyecto articula interfaces, servicios, persistencia relacional, transacciones,
auditoría y programación PL/SQL en un caso de uso universitario. Permite explicar decisiones
del modelo mediante restricciones, consultas y flujos verificables.

**Operativa.** La información se organiza por materia y clase, con consulta diferenciada por
rol e historial de cambios. La propuesta busca reducir inconsistencias y facilitar revisión;
no se atribuye un ahorro de tiempo cuantificado que todavía no ha sido medido.

**Técnica.** Las reglas se distribuyen entre validación Python, servicios, paquetes y restricciones
Oracle. La confirmación atómica y las claves de idempotencia protegen frente a operaciones
parciales o repetidas.

**Inclusión y control.** Las excepciones permiten un acceso alternativo autorizado sin ocultar
que la verificación no fue biométrica. La revisión manual evita transformar problemas de
captura en ausencias definitivas.

## 3. Objetivos

### 3.1 Objetivo general

Desarrollar una plataforma académica que integre la gestión de asignaturas, matrículas y
sesiones de clase con el registro y seguimiento de asistencia, incorporando control de acceso,
revisión docente y trazabilidad en Oracle.

### 3.2 Objetivos específicos

1. Definir un modelo relacional que vincule docentes, estudiantes, materias, matrículas,
   clases y resultados de asistencia.
2. Proporcionar portales con funciones y restricciones específicas para los tres roles.
3. Integrar el reconocimiento facial y de voz como apoyo al registro, con validación de
   muestras y tratamiento explícito de resultados desconocidos o fallidos.
4. Permitir revisión y confirmación de resultados por clase, controlando duplicados y reintentos.
5. Registrar correcciones, retiros, archivo y acciones administrativas con actor y motivo.
6. Ofrecer al estudiante un perfil privado con indicadores acumulados, detalle por materia
   y calendario mensual.
7. Incorporar un acceso excepcional autorizado y diferenciarlo de la verificación biométrica.
8. Mantener instalación, respaldos, recuperación, pruebas y documentación reproducibles,
   incluyendo el estudio visual del modelo en SQL Developer.

### 3.3 Resultados esperados y forma de comprobarlos

| Resultado | Evidencia de comprobación |
| --- | --- |
| Clase y resultado identificables | Claves, FK y unicidad por clase/estudiante. |
| Operaciones completas y no duplicadas | Confirmación atómica y pruebas de reintento/concurrencia. |
| Revisión trazable | Detección inicial, decisión final, motivo y auditoría. |
| Acceso por rol | Validación de sesión y pruebas de restricciones de navegación/servicios. |
| Excepción diferenciada | Estado persistente y eventos de autorización/acceso/revocación. |
| Comprensión y entrega | Guías, catálogo de consultas, modelo DDL y ensayo de recuperación. |

## 4. Alcance, actores y requisitos

### 4.1 Alcance actual

La implementación comprende gestión de cuentas y materias, matrícula, clases, asistencia,
reconocimiento asistido, historial, sesiones globales, administración y perfiles de estudiante
y docente. Incluye agenda, configuración docente y excepciones de acceso; el esquema es 009.

El login institucional general del estudiante y el ensayo integral con personas siguen
pendientes. Se descartó el correo: la clave de excepción se entrega manualmente. El
reconocimiento no incorpora una prueba de presencia real demostrada.

### 4.2 Actores

| Actor | Responsabilidad principal | Restricción relevante |
| --- | --- | --- |
| Docente | Gestionar materias, agenda, clases, asistencia y excepciones de sus alumnos. | Debe ser propietario de la materia y tener cuenta activa. |
| Estudiante | Inscribirse, consultar sus registros y acceder a su perfil. | Su identidad validada determina los datos que puede consultar. |
| Administrador | Gestionar cuentas/materias, consultar/exportar auditoría y autorizar excepciones. | El historial no tiene edición o borrado desde el panel administrativo. |
| Responsable técnico de Oracle | Preparar infraestructura, permisos, copias y recuperación. | Es una función operativa, no un cuarto rol del portal. |

### 4.3 Requisitos funcionales

| ID | Requisito | Estado |
| --- | --- | --- |
| RF-01 | Alta y acceso docente con credenciales y autorización privada de alta. | Implementado |
| RF-02 | Acceso estudiantil facial y alta con código institucional. | Implementado |
| RF-03 | Materias, secciones, matrícula, retiro y archivo con historial. | Implementado |
| RF-04 | Apertura/reutilización de clase por materia e instante. | Implementado |
| RF-05 | Análisis facial o de voz y revisión de la decisión por estudiante. | Implementado; calibración real pendiente |
| RF-06 | Confirmación única de propuesta completa e idempotencia. | Implementado |
| RF-07 | Consulta de asistencia y perfil estudiantil con calendario. | Implementado; aceptación visual pendiente |
| RF-08 | Administración mixta: consulta/exportación y edición controlada. | Implementado |
| RF-09 | Sesiones únicas, caducidad y revocación en servidor. | Implementado |
| RF-10 | Recuperación de contraseña docente con autorización privada. | Implementado; funcionamiento confirmado por el usuario |
| RF-11 | Excepción de identidad con documento, contraseña y aprobación vigente. | Implementado; ensayo institucional pendiente |
| RF-12 | Autorizar excepciones de alumnos matriculados y entregar manualmente la clave. | Implementado en 009; correo descartado |
| RF-14 | Perfil docente con todas sus materias, calendario de clases y próximas sesiones. | Implementado; aceptación en Render a cargo del usuario |
| RF-15 | Configuración docente separada del portal para archivar cuenta/materias. | Implementado |
| RF-13 | Login institucional general del estudiante. | Pendiente |

### 4.4 Requisitos de calidad

| Área | Criterio adoptado | Límite actual |
| --- | --- | --- |
| Integridad | PK, FK, CHECK, índices únicos y transacciones. | El propietario Oracle conserva facultades superiores a los roles web. |
| Acceso | Identidad validada, permiso por rol, sesión revocable y caducidad. | Separación cloud verificada; el propietario conserva privilegios de mantenimiento. |
| Privacidad | Secretos fuera de Git, hashes y plantillas sin fotos/audio de registro persistidos en tablas. | Retención y operación institucional deben formalizarse antes del despliegue real. |
| Usabilidad | Jerarquía institucional, foco visible, navegación consistente y adaptación de pantallas. | La aceptación del frontend sigue abierta. |
| Portabilidad | Rutas del proyecto y preparación de venv por equipo. | Validación completa en otro PC/plataforma pendiente. |
| Mantenimiento | Servicios compartidos, migraciones y documentación temática. | La licencia y la entrega general continúan en el roadmap. |

## 5. Arquitectura y organización

La entrada es `principal.py`. El router selecciona la vista, mientras la identidad procede de
la sesión validada, no de la URL. Las pantallas utilizan componentes comunes; los servicios
coordinan reglas y los repositorios conectan con Oracle.

<!-- FIGURA_ARQUITECTURA -->

### 5.1 Capas

| Capa | Ubicación | Responsabilidad |
| --- | --- | --- |
| Entrada/navegación | principal.py y src/interfaz | Rutas, identidad visual y presentación de portales. |
| Interfaz | src/pantallas y src/componentes | Formularios, resultados, menús, perfil y mensajes. |
| Aplicación | src/servicios | Validaciones, coordinación, autenticación, identidad y revisión. |
| Biometría | src/canalizaciones y utilidades de muestras | Extracción, comparación y tratamiento de captura/audio. |
| Persistencia | src/base_datos | Pool, consultas, llamadas PL/SQL, transacción y recuperación. |
| Catálogo SQL | sql/consultas y src/base_datos/consultas.py | Sentencias externas, caché, validación de rutas y plantillas de identificadores. |
| Reglas Oracle | sql y sql/migraciones | Estructura, paquetes, triggers, vistas y verificación. |
| Operación cloud | Dockerfile, deploy y scripts de preparación | Imagen Linux, proxy HTTPS, configuración privada y verificación previa al arranque. |

### 5.2 Decisiones relevantes

- Las reglas sensibles se comprueban en servidor; un botón deshabilitado no es el control definitivo.
- Las conexiones del pool limpian contexto para no heredar el actor de una operación anterior.
- La sesión web y la conexión Oracle son conceptos diferentes.
- Una propuesta biométrica se revisa antes de persistir la confirmación de una clase.
- Una operación de escritura con resultado incierto no se repite indiscriminadamente.
- Las vistas simplifican consultas; el control de filas por usuario depende del contexto y los servicios.

### 5.3 Organización de las consultas

La reorganización del 21 de noviembre extrae 104 apariciones de SQL de nueve módulos
a un catálogo de 88 sentencias únicas y dos plantillas de identificadores. Las consultas
iguales se comparten; se conservan sus parámetros, texto y límites de transacción.
`cargar_sql` lee archivos UTF-8 dentro del catálogo y mantiene caché. Las plantillas
validan nombres Oracle; los datos continúan enviándose mediante parámetros enlazados.

El catálogo no sustituye a `oracle_scripts.sql`, las migraciones ni los paquetes PL/SQL.
Tampoco traslada por sí mismo las reglas de negocio de Python a Oracle. La generación
dinámica de DDL en las herramientas de respaldo es una excepción técnica documentada
para revisar más adelante. No se afirma que todo SQL de cualquier herramienta haya desaparecido.
Detalle: [catálogo SQL](../sql/consultas/README.md).

## 6. Flujos funcionales

### 6.1 Alta y acceso docente

La herramienta de preparación genera una autorización privada de alta. El docente proporciona
usuario, nombre, contraseña y autorización. Python valida y guarda bcrypt. El login compara
la contraseña y utiliza límites de intentos; la sesión se abre en el registro compartido.
La recuperación cambia la contraseña con autorización válida y revoca accesos previos.

### 6.2 Acceso y registro del estudiante

Una captura facial debe contener exactamente un rostro completo y una muestra válida. La
comparación identifica o rechaza; una identidad existente abre sesión mediante prueba de
acceso y estado confirmado. El registro requiere nombre y código institucional. La voz es
opcional; si se aporta, debe superar sus validaciones antes de guardar.

El acceso actual comprueba un factor facial. Tener dos plantillas almacenadas no equivale
a haber completado dos factores de autenticación. El login institucional general sigue pendiente.

### 6.3 Materia, grupo y matrícula

Una materia pertenece a un docente y contiene su sección. Un código o enlace de inscripción
localiza la materia; el QR transporta ese enlace, no una credencial ni una tabla adicional.
El alta crea la relación de matrícula y el trigger registra su historial. Un retiro elimina
la relación actual sin borrar al estudiante o su asistencia anterior.

### 6.4 Preparación, revisión y confirmación de clase

1. El docente selecciona materia y abre o reutiliza una clase con fecha/hora.
2. Se reciben fotos o audio y se valida la entrada.
3. El motor genera una propuesta con identidad y estado de detección.
4. El docente revisa decisiones y motivos; los identificadores y la detección inicial permanecen protegidos.
5. El servidor verifica clase, propietario, matrícula completa, estados y propuesta.
6. Oracle inserta todos los resultados y confirma la clase en una transacción.
7. Un reintento con igual clave y contenido reconoce la confirmación existente.

<!-- FIGURA_FLUJO -->

### 6.5 Interpretación de resultados

| Estado original | Interpretación | Tratamiento |
| --- | --- | --- |
| PRESENTE | Se completó un análisis con coincidencia. | Propuesta de presente; revisión permitida con motivo. |
| AUSENTE | Análisis completado sin coincidencia según el flujo. | Propuesta revisable, no certeza de ausencia física. |
| SIN_MUESTRA | No existe una plantilla utilizable para ese estudiante/modalidad. | Decisión manual y motivo obligatorios. |
| ANÁLISIS FALLIDO | No se pudo procesar la captura/audio de forma válida. | No confirmable; no se transforma en ausencia. |

Una corrección posterior modifica la decisión final mediante el procedimiento auditable.
La detección y la revisión inicial se conservan; el historial registra actor, motivo y valores.

### 6.6 Portales, perfiles y configuración

El portal docente concentra tomar asistencia, gestionar materias, consultar registros y
autorizar excepciones. Su perfil presenta identidad, todas sus materias activas/archivadas,
agenda mensual, detalle diario y próximas sesiones ya creadas. Una materia no genera clases
semanales por sí sola: una fecha futura aparece al crear ese horario. Programar una clase
no confirma presencia. El selector omite el ID global y conserva su estado por docente/materia.

La configuración docente reúne el archivo de materias/cuenta, con motivo y confirmación.
Archivar conserva el historial. No se añade borrado físico de cuentas desde este panel.

El portal del estudiante sirve para administrar sus matrículas; su perfil muestra identidad,
porcentaje acumulado, materias, asistencias, ausencias y calendario. El acumulado usa clases
confirmadas, no el promedio simple de porcentajes de cada materia. Se utiliza America/Bogota.

La consulta obtiene al actor desde una sesión validada y contrasta el contexto Oracle. Una
URL no permite elegir otro estudiante o docente. Los perfiles usan jerarquías y presentaciones
distintas: historial de asistencia para el alumno y agenda de clases para el profesor.

### 6.7 Administración

El administrador consulta/exporta auditoría y edita cuentas o materias con motivo y versión
de edición. Una versión obsoleta se rechaza. La conexión técnica utiliza paquetes autorizados
y vistas de historial; no ofrece modificación o borrado de auditoría desde la interfaz.

### 6.8 Excepción biométrica y entrega manual

En Portal docente → Excepciones de acceso, el profesor selecciona una materia propia activa
y un alumno activo matriculado. Comprueba el documento, define categoría, referencia y vigencia
y establece una clave de al menos 12 caracteres, con confirmación. La entrega es personal;
se descartó el correo. El formulario limpia documento y clave después de autorizar.

El docente puede renovar/revocar sus autorizaciones, pero no sustituir las de otro docente
o de Administración. Administración conserva capacidad de revisión y sustitución. El paquete
comprueba rol, actividad, propiedad de materia, matrícula, versión y autoría en Oracle.

El estudiante accede con tipo/número de documento y contraseña, sin necesitar una captura.
La autorización y el último resultado de identidad son datos diferentes: EXCEPCIONAL conserva
el método real. Revocar, renovar o vencer una autorización invalida accesos/pruebas anteriores.
Iniciar sesión por excepción no registra asistencia.

Para la demostración se preparó una clave común en un archivo privado equivalente al de
alta docente. Se asigna al autorizar individualmente a cada alumno de prueba; cada uno usa
su propio documento. El valor de esa clave no forma parte de esta memoria ni del repositorio.

## 7. Modelo de datos y PL/SQL

El núcleo relaciona profesores, materias, matrículas, estudiantes, clases y resultados.
Historiales, eventos, límites, sesiones, administradores y verificaciones completan el modelo.
La guía completa se incorpora en el anexo A.

<!-- FIGURA_MODELO -->

### 7.1 Entidades

| Grupo | Tablas | Finalidad |
| --- | --- | --- |
| Cuentas | PROFESORES, ESTUDIANTES, ADMINISTRADORES | Identidad y actividad de los tres roles. |
| Organización académica | MATERIAS, MATERIA_ESTUDIANTES, CLASES | Asignatura/sección, matrícula y sesión académica. |
| Resultados | REGISTROS_ASISTENCIA | Una decisión final por estudiante y clase. |
| Historia | AUDITORIA_ASISTENCIA, HISTORIAL_MATRICULAS, EVENTOS_GESTION | Rastro de cambios, retiros y operaciones. |
| Seguridad | LIMITES_ACCESO, SESIONES_USUARIO, VERIFICACION_ESTUDIANTES | Intentos, vigencia de acceso y método de verificación. |
| Evolución | VERSIONES_ESQUEMA | Control de instalación y migraciones. |

### 7.2 Reglas del modelo

La matrícula usa una PK compuesta; la asistencia es única por clase/estudiante. La FK compuesta
de clase/materia impide cruzar resultados entre asignaturas. El horario se normaliza a UTC.
Las referencias históricas y el rol/actor de sesiones pueden ser lógicas sin FK; el diagrama
no debe inventar relaciones físicas que la base no tiene.

El archivo de una cuenta es diferente de borrarla físicamente. Existen FK con cascada, por lo
que borrar padres directamente puede destruir datos relacionados. Los flujos de la aplicación
utilizan archivo/retiro según la acción y conservan el historial correspondiente.

### 7.3 Paquetes y disparadores

Los ocho paquetes son PKG_AUDITORIA, PKG_ASISTENCIA, PKG_GESTION, PKG_CLASES,
PKG_ADMINISTRACION, PKG_SESIONES, PKG_EXCEPCIONES y PKG_EXCEPCIONES_DOCENTES.
Sus especificaciones contienen 38 rutinas
públicas. Validan contexto, propiedad, actividad, motivos, confirmación y sesión según el caso.

Los diez triggers actualizan fechas/versiones, protegen identidad de clases/resultados,
exigen actividad y crean historiales. No son tareas programadas. Los eventos de acceso y
excepción se escriben desde servicios/paquetes; no existe un trigger general para todo el SQL.
La transacción pertenece al llamador: los historiales se confirman o revierten con la acción.

### 7.4 Evolución y visualización

Las versiones 001–009 incorporan estructura, auditoría, clases, estados, gestión,
administración, sesiones y excepciones. 009 añade dos relaciones de aprobación docente
y el paquete correspondiente, preservando las autorizaciones previas y los datos académicos.

`oracle_scripts.sql` conduce a la instalación nueva; una base existente evoluciona mediante
migraciones, con respaldo previo. SQL*Plus y SQL Developer son clientes, no almacenes de datos.

El catálogo interactivo y el diccionario se generan desde metadatos Oracle, sin filas de
personas. Incluyen 14 tablas y 11 FK físicas. El DDL modelo_008 es un artefacto histórico;
para ver 009 se utiliza el catálogo vigente o el diccionario de la base instalada.

## 8. Seguridad, privacidad y reconocimiento

### 8.1 Controles de acceso

Las contraseñas se guardan como hashes bcrypt. El token de sesión se representa en Oracle
con SHA-256; una cuenta tiene una sesión vigente, con treinta minutos de inactividad y ocho
horas máximas. Las operaciones vuelven a comprobar revocación, cuenta y vigencia.

El documento alternativo se identifica con HMAC y últimos cuatro caracteres. La prueba de
acceso firmada dura 90 segundos y su versión impide reutilizar una acreditación anterior.
El documento por sí solo no es un autenticador. Los límites persisten en Oracle: cinco fallos
y quince minutos de bloqueo en los ámbitos de acceso que los implementan.

### 8.2 Tratamiento de biometría

La base almacena vectores JSON, no las fotos o grabaciones de registro. Python valida formato,
dimensiones, valores finitos y calidad básica. El descriptor facial conserva su escala;
el de voz se normaliza a norma L2. Un JSON válido en Oracle no demuestra que un vector sea
válido o que pertenezca a la persona que intenta entrar.

La identificación facial compara distancias y la voz similitud coseno, con umbral absoluto y
margen entre identidades. Los empates se rechazan; un puntaje no es una probabilidad de certeza.
Los valores iniciales requieren calibración y evaluación con muestras consentidas separadas.

### 8.3 Secretos, respaldo y recuperación

Las credenciales y claves se mantienen en configuración privada. El repositorio excluye venv,
certificados, claves, datos privados, exportaciones y respaldos. Las copias V2 cifran datos/DDL
con AES-GCM y autentican su manifiesto con HMAC-SHA256. La restauración exige un destino vacío
y comprueba integridad, estructura y datos antes de promover una copia.

La clave de respaldo y la de identidad son distintas y deben conservarse mediante el procedimiento
privado correspondiente. Restaurar las filas de verificación sin recuperar la clave HMAC
original impide resolver correctamente los documentos registrados. Los tokens restaurados se revocan.

### 8.4 Límites que continúan abiertos

La identificación facial no tiene una protección de presencia real demostrada: una fotografía
puede engañar el acceso. También quedan pendientes evaluación con voces externas, dispositivos,
ruido y otras condiciones reales. La interfaz administrativa no vuelve inmutable la auditoría
frente al propietario Oracle. La separación de cuentas cloud está verificada. La retención, el consentimiento,
la evaluación biométrica y la operación institucional requieren preparación adicional.

## 9. Interfaz e identidad institucional

La marca de la plataforma es **UPC | Aula**, separada del logosímbolo universitario. Se emplean
recursos originales del manual de identidad, sin redibujar ni recolorear símbolos. El verde
principal del proyecto es #007337, con blanco y superficies neutras; Arial proporciona la
tipografía de interfaz. El lema Educación y Futuro tiene una posición secundaria.

El encabezado comparte navegación y cuenta. El logotipo/Inicio conservan la sesión; el menú
incluye Mi perfil, Configuración y Cerrar sesión según disponibilidad. La portada tiene
composición institucional y acceso por rol. El pie académico es común a las pantallas.

<!-- FIGURA_PORTADA -->

La revisión incluye tamaños de escritorio y móvil, foco visible y comportamientos del menú.
El usuario confirmó identidad actual, iconos/contraseñas, recuperación docente y el separador
de Cerrar sesión. Otros recorridos y pantallas siguen pendientes de aceptación expresa.
El pie identifica a Rafael Camilo Rodriguez Ayala, Harold Steven Torres Diaz y Oscar William
Rivero Ordoñez, con referencia docente de Amilkat Sierra Romano. Se ocultan los controles
de enlace al ancla de los encabezados, manteniendo la navegación y los títulos.

La revisión del 21 de noviembre corrige la dependencia de la fuente nativa de iconos en
Chrome mediante una fuente local. En Firefox se ajusta el ancho efectivo del pie compartido
con un ResizeObserver. La comprobación posterior comprende 173 vistas en Firefox, Edge,
Chrome y Brave. Los tamaños móviles son viewports de escritorio, no teléfonos físicos.
Los recorridos autenticados emplean fixtures con Oracle bloqueado. En Firefox se omite
la comprobación visual de foco de dos formularios por ventana inactiva de automatización;
las acciones de teclado sí se comprobaron. No equivale a certificar accesibilidad completa,
Safari ni cámara y micrófono físicos. Evidencia: [frontend](FRONTEND.md).

## 10. Instalación y operación

### 10.1 Entorno

El entorno verificado es Windows x64 con Python 3.11 y Oracle XE 18c / XEPDB1. Las dependencias
directas están fijadas en requirements.txt y existe un snapshot Windows en
requirements-lock-windows-py311.txt. La instalación en otras plataformas debe validarse.

El venv se crea en cada equipo. La preparación de Oracle genera configuración privada y
realiza la instalación nueva en un esquema vacío; una base existente se actualiza con migraciones.
No se requiere copiar los archivos físicos de Oracle para abrir SQL Developer.

### 10.2 Secuencia de una instalación nueva local

```powershell
.\preparar_entorno.cmd
.\.venv\Scripts\python.exe scripts\preparar_oracle.py --os-auth --pdb XEPDB1
.\.venv\Scripts\python.exe scripts\preparar_identidad.py
.\.venv\Scripts\python.exe scripts\preparar_alta_docente.py
.\.venv\Scripts\python.exe scripts\preparar_administracion.py
.\iniciar.cmd
```

La secuencia supone Oracle local preparado y acceso SYSDBA para el paso de creación, no para
el uso ordinario del portal. Para una base remota o ya configurada se utiliza la guía de
instalación. Este informe no ejecuta esos comandos ni crea cuentas.

### 10.3 HTTPS y diagnóstico

El arranque local sirve en https://localhost:8501 con los certificados del equipo. La confianza
de esa CA se configura en el navegador; después de importarla se reinicia el navegador.
Para un teléfono, localhost identifica al propio teléfono: se necesita dirección LAN y la
configuración de red/certificado indicada en la guía de instalación.

```powershell
.\.venv\Scripts\python.exe scripts\diagnostico.py
.\.venv\Scripts\python.exe scripts\oracle.py verificar
```

La operación debe diferenciar verificar, respaldar, migrar e instalar. Los laboratorios y
pruebas de integración pueden escribir fixtures aunque luego reviertan; no se confunden con
una revisión estrictamente de solo lectura.

### 10.4 Oracle Autonomous y cuentas técnicas

UPCAula tiene instaladas y verificadas las versiones 001–009. Se preservan 14 tablas,
11 vistas y 10 triggers; hay ocho paquetes/cuerpos válidos. La migración 009 se aplicó
en Oracle local y Autonomous después de respaldos cifrados y verificados.

| Cuenta técnica | Finalidad | Alcance |
| --- | --- | --- |
| UPC_ASISTENCIA | Propietario del esquema | Instalación, migración, respaldo y catálogo. |
| UPC_AULA_APP | Runtime ordinario | Contrato de 53 permisos; ORACLE_ESQUEMA identifica el propietario. |
| UPC_ADMIN_APP | Operaciones restringidas | Cinco EXECUTE y lectura de tres vistas de auditoría; sin DML directo de aprobación. |

La validación real de la sesión precede al uso de la cuenta restringida. Para excepciones
docentes se establece contexto PROFESOR; el paquete administrativo continúa exigiendo
ADMINISTRADOR. Las cuentas de la web son identidades funcionales distintas de las de Oracle.

### 10.5 Despliegue en Render

Render construye el Docker del repositorio y sirve Streamlit. Oracle permanece en
Autonomous y la conexión utiliza TCPS/TLS. La ACL de la base permite las redes de
salida configuradas en Render. La URL de la web es distinta del DSN de Oracle.

<!-- FIGURA_CLOUD -->

El proceso de arranque comprueba configuración, clave HMAC original, esquema 001–009,
objetos válidos y permisos. La clave se proporciona mediante un archivo secreto; su
formato Base64 se decodifica a los 32 bytes originales. No se sustituye por una clave nueva.

Auto-Deploy On Commit toma los commits publicados en la rama conectada. El flujo de trabajo
es MD → commit local → push. El commit por sí solo no actualiza Render. Las variables y
archivos secretos se administran por separado y permanecen fuera del repositorio.

### 10.6 Recursos, evidencia y límites de operación

Hay evidencia de un despliegue Live del commit 20ed6be con Oracle/permisos comprobados y
HTTP 200/ok de salud. Se publicaron después optimizaciones, perfiles y la versión 009.
El resultado del último despliegue y la aceptación de pantallas corresponden al usuario.
No se declara que un healthcheck valide reconocimiento o disponibilidad continua de Oracle.

La aplicación conserva las fotos comprimidas originales y crea miniaturas solo para mostrar.
Al analizar, decodifica el original; los píxeles usados por el reconocimiento se mantienen.
La voz reutiliza el clasificador por grabación y lee audio por bloques. En una imagen sintética
2048×1536 el almacenamiento pasó de 9.437.184 a 2.428.600 bytes; esto no equivale a una
reducción medida de toda la RAM del servidor. Falta medir CPU, memoria y concurrencia en Render.

La VM OCI no se usa para esta entrega. Vercel queda descartado: solo Render para la web y
Autonomous para los datos. Las pruebas de página, cámara y voz quedan al usuario; este PC
no tiene cámara. No se automatiza un ensayo físico desde este equipo.

## 11. Verificación y evidencias

### 11.1 Estrategia y resultados registrados

Las pruebas de reglas, interfaz y Oracle se distinguen de una medición de precisión facial
o de voz. Los datos sintéticos se eliminan/revierten por los procedimientos de cada ensayo.
Esta actualización documental no vuelve a ejecutar pruebas de la página ni usa cámara.

| Evidencia | Resultado | Alcance y límite |
| --- | --- | --- |
| Batería del 22/11 | 293 pruebas; 288 aprobadas y 5 omitidas. | Las omitidas requieren un usuario Oracle temporal limitado y no cuentan como aprobadas. |
| Excepciones docentes | 7 pruebas de reglas/Oracle y 3 de interfaz aprobadas dentro de esa batería. | Propiedad, matrícula, autoría, versión, revocación y vencimiento. |
| Perfil docente | 5 pruebas de perfil y 8 de navegación registradas. | Aislamiento, agenda, identidad y rutas; no certifican aceptación en Render. |
| Oracle 009 | Local y Autonomous verificados; sin errores ni objetos inválidos. | Comprobación de estructura y compilación; respaldo cifrado previo a migrar. |
| Runtime cloud | Preflight real: 53 permisos y cinco paquetes administrativos autorizados. | Contrato de acceso comprobado, separado del uso del propietario. |
| Catálogo vigente | 14 tablas, 140 columnas y 11 FK; 128 enlaces locales revisados. | Metadatos del esquema; sin filas de personas ni contraseñas. |
| Despliegue | Evidencia Live de 20ed6be; publicaciones posteriores en GitHub. | El último despliegue queda por comprobar por el usuario. |
| Evidencia histórica | 173 vistas entre navegadores y ensayo de restauración 008 en dos esquemas temporales. | Fechados y separados; no son otra ejecución de 009 ni un ensayo físico actual. |

La lectura de la evidencia técnica no permite deducir exactitud biométrica poblacional,
ahorro de tiempo, reducción del abandono ni cumplimiento institucional de la solución.

### 11.2 Aceptación y criterios de cierre

Una función puede estar implementada y probada sin haber sido aceptada por el usuario. El cierre
requiere comprobar el recorrido previsto, mensajes, permisos, resultado persistido y recuperación
ante fallos, además de la conformidad visual cuando corresponda.

Para el ensayo final se prevé incluir cámara/micrófono, desconocidos y muestras ausentes,
varias pestañas y dispositivos, QR/LAN, revocación, exportación, copias y restauración.
La calibración debe separar sus muestras de las de evaluación y registrar FAR, FRR y confusiones
solo cuando existan grupos de datos suficientes. No se declara una precisión biométrica medida.

## 12. Roadmap, riesgos y continuidad

### 12.1 Un roadmap general con ramas

| Rama | Entregables | Estado |
| --- | --- | --- |
| Frontend/backend | Selector por docente/materia, créditos, perfiles, configuración y excepciones manuales. | Implementados y probados; prueba de la página a cargo del usuario. |
| Base de datos | Visualización de 14 tablas, diccionario de 140 columnas, conexión y goodwill. | Documentados y contrastados con 009; revisión académica del equipo pendiente. |
| Evolución | Calidad, recursos y mejoras posteriores dentro de Render. | Propuestas; Vercel descartado. |
| Historial de despliegue | Plan anterior con evidencia y pendientes conservados. | Continúan la decisión sobre datos, QR/persistencia y ensayo final. |

El punto de entrada es ROADMAP.md; las ramas frontend/backend y base de datos mantienen
criterios de cierre. ROADMAP_HISTORICO.md preserva decisiones y entregas anteriores.

### 12.2 Cadencia y aceptación

Se registran los cambios en Markdown antes de confirmar. Los cambios mayores tienen
commit propio; se agrupan tres cambios menores por commit. Se publica al completar cinco
cambios o un punto del roadmap, salvo una instrucción expresa del usuario que adelante el paso.
La configuración y las claves privadas no se incluyen en los commits.

La prueba de la página, cámara, voz y reconocimiento corresponde al usuario. La documentación
registra el estado técnico sin convertirlo en aceptación visual o validación institucional.

### 12.3 Riesgos y continuidad

| Riesgo | Consecuencia | Tratamiento |
| --- | --- | --- |
| Captura, ruido o suplantación no evaluados | Coincidencias o rechazos incorrectos. | Revisión docente, acceso alternativo y evaluación con muestras consentidas. |
| Confundir sin muestra con ausencia | Decisión académica equivocada. | Estados distintos; resolución manual con motivo. |
| Reintentos o concurrencia | Duplicados y confirmaciones parciales. | Transacción, bloqueos, versiones e idempotencia. |
| Pérdida de secretos | Copias o documentos no recuperables. | Custodia de claves originales y ensayo de recuperación. |
| Recursos insuficientes | Latencia o reinicio al cargar modelos. | Medir memoria/CPU/concurrencia en el Render utilizado. |
| Clave común de prueba | Reutilización entre alumnos de demostración. | Autorización individual y vigencia; sustituirla antes de uso institucional. |
| Evidencia insuficiente de beneficio | Promesas comerciales sin respaldo. | Piloto medido; distinguir hipótesis de resultados observados. |

La evolución del esquema se realiza con migraciones versionadas y respaldo previo. Esta
edición y la presentación comercial utilizan solo archivos/documentación, sin modificar la base.

## 13. Glosario y referencias del proyecto

### 13.1 Glosario

| Término | Significado en UPC Aula |
| --- | --- |
| Autenticación | Comprobar la identidad para abrir acceso. |
| Autorización | Determinar qué acciones permite una identidad o un permiso excepcional. |
| Asistencia | Decisión académica final vinculada a estudiante y clase. |
| Plantilla biométrica | Vector derivado de una muestra; sigue siendo información sensible. |
| Hash | Representación utilizada para comprobar un valor sin guardar su texto recuperable. |
| HMAC | Huella autenticada con una clave privada; se utiliza para el documento. |
| Idempotencia | Repetir la misma solicitud válida sin duplicar su efecto. |
| Transacción | Conjunto de cambios que se confirma o revierte conjuntamente. |
| Trigger | Regla automática que se ejecuta ante una operación sobre una tabla. |
| Vista | Consulta almacenada; no es un diagrama ni una copia independiente de las filas. |
| Migración | Cambio versionado que evoluciona un esquema existente. |
| DDL | Sentencias de definición de estructura; importarlas como modelo no equivale a ejecutarlas. |
| READ ONLY | Transacción de consulta que impide escrituras ordinarias sobre los datos. |
| FAR / FRR | Tasas de aceptación incorrecta y rechazo incorrecto en conjuntos de evaluación definidos. |

### 13.2 Fuentes internas y trazabilidad

| Fuente | Contenido |
| --- | --- |
| docs/ROADMAP.md | Prioridades, decisiones y pendientes. |
| docs/ROADMAP_2.md | Mejoras visuales y revisión futura de reglas, paquetes y modelo. |
| docs/DESPLIEGUE.md | Docker, Caddy, TLS con Autonomous, configuración privada y ensayo público. |
| sql/consultas/README.md | Catálogo externo y separación entre consultas e instalación. |
| docs/BASE_DE_DATOS.md | Funcionamiento, reglas y consultas; anexo A. |
| docs/DICCIONARIO_DATOS.md y docs/base_datos/catalogo.json | Metadatos 009, columnas y restricciones; anexo B. |
| docs/CONEXION_BASE_DATOS.md | Recorrido Render, pools, TLS y cuentas técnicas. |
| docs/PERFIL_DOCENTE.md | Agenda y configuración del docente. |
| docs/GOODWILL.md | Valor, beneficios esperados, indicadores y aporte académico. |
| docs/PORTAL_Y_SESIONES.md | Navegación, sesiones y validación compartida. |
| docs/REGLAS_NEGOCIO.md | Gestión de cuentas, matrícula, archivo y biometría. |
| docs/CLASES_Y_REVISION.md | Apertura, revisión y confirmación de clases. |
| docs/ESTADOS_DETECCION.md | Presente, ausente, sin muestra y análisis fallido. |
| docs/VALIDACION_MUESTRAS.md | Validación de archivos, audio y vectores. |
| docs/RECONOCIMIENTO.md | Comparación, rechazo, evaluación y límites. |
| docs/EXCEPCIONES_BIOMETRICAS.md | Autorizaciones, estados, pruebas y auditoría de excepción. |
| docs/ADMINISTRACION.md | Alcance del tercer rol y conexión limitada. |
| docs/PERFIL_ESTUDIANTE.md | Cálculo de indicadores y calendario privado. |
| docs/RECUPERACION_ACCESO.md | Restablecimiento docente. |
| docs/RECUPERACION.md | Copias, restauración y retención. |
| docs/IDENTIDAD_VISUAL.md y docs/FRONTEND.md | Diseño, recursos y aceptación. |
| docs/INSTALACION.md y docs/SQLPLUS_Y_SQLDEVELOPER.md | Preparación, operación y presentación de la base. |
| docs/CAMBIOS.md | Registro de entregas. |

Los scripts, repositorios y paquetes son la referencia ejecutable del funcionamiento. El catálogo del 22 de noviembre contrasta Autonomous 009 y se complementa con la guía
funcional iniciada el 18/11.
La documentación conserva evidencias locales de pruebas; esas evidencias y los secretos no
se incorporan a este PDF. Los archivos de configuración públicos contienen ejemplos, no valores reales.

### 13.3 Recursos institucionales y bibliografía técnica

El logotipo y sus proporciones proceden del Manual de Identidad Visual UPC de 2010, disponible
en Proyecto_recursos. Su procedencia se detalla en static/img/upc/README.md. No se creó un símbolo
universitario alternativo. Los diagramas explican la organización funcional; esta edición no
incluye nuevas capturas de la página ni pruebas de cámara.

- Universidad Popular del Cesar. Manual de Identidad Visual, 2010. Recurso local del proyecto.
- Oracle. Data Modeler Concepts and Usage, 24.3. Importación desde DDL y diccionario.
- Oracle. SQL Developer Concepts and Usage, 18.3. Integración de Data Modeler.
- Oracle. Database Installation Guide for Microsoft Windows, 18c. Tablespaces y archivos de datos.

Las referencias web completas aparecen junto a los procedimientos correspondientes del anexo A.
Las rutas de código de esta memoria son relativas a la raíz del repositorio ControlAsistenciaUPC.

## 14. Valor, beneficios y aporte académico

UPC Aula integra la actividad de clase y su trazabilidad. Para el docente, centraliza
materias, sesiones y revisión; para el estudiante, acceso e historial; para la gestión,
consulta y auditoría. Su contribución académica incluye modelado relacional, PL/SQL,
transacciones, seguridad, migraciones y recuperación.

Los ahorros de tiempo, la conveniencia comercial y la escalabilidad son hipótesis que se
validarán en un piloto. No hay ingresos, valoración empresarial ni tamaño de mercado
medidos. La presentación comercial propone una conversación de piloto e inversión futura;
no declara una oferta pública de acciones ni una vinculación empresarial oficial de la UPC.

| Beneficio esperado | Indicador del piloto | Evidencia pendiente |
| --- | --- | --- |
| Menos tiempo de consolidación | Minutos por clase frente a lista manual. | Ensayo comparable y varias repeticiones. |
| Continuidad de acceso | Solicitudes resueltas y tiempo de autorización. | Recorrido docente/alumno con vigencia y revocación. |
| Trazabilidad | Correcciones con actor, motivo y fecha. | Consulta de auditoría sobre casos del piloto. |
| Operación viable | CPU/RAM, latencia y concurrencia. | Métricas del plan Render utilizado. |
| Viabilidad económica | Costo operativo por clase confirmada. | Costos reales y volumen de uso medidos. |

La adopción requiere definir consentimiento, retención, responsabilidades y condiciones de
uso. La identidad UPC se conserva como referencia académica; un proyecto del equipo no
equivale por sí solo a un producto aprobado oficialmente por la universidad.

La guía [GOODWILL.md](GOODWILL.md) desarrolla el valor por actor, sus límites y los indicadores.
La presentación utiliza el mismo estado de evidencia y evita inventar métricas comerciales.
