# Documentación integral del proyecto UPC | Aula

Edición documental 1.0 · 18 de noviembre de 2026 · Esquema Oracle 001–008.

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

| Aspecto | Situación al corte documental |
| --- | --- |
| Identidad | UPC \| Aula, con recursos institucionales originales y lema Educación y Futuro. |
| Entorno verificado | Windows x64, Python 3.11 y Oracle XE 18c / XEPDB1. |
| Persistencia | 14 tablas, 138 columnas visibles, 9 FK, 11 vistas y 7 paquetes PL/SQL. |
| Reglas automáticas | 10 disparadores habilitados; sin objetos inválidos ni errores de compilación en la consulta registrada. |
| Verificación de software | Última publicación completa: 217 pruebas aprobadas con Oracle habilitado. |
| Revisión de estructura | 43 SELECT validados el 18 de noviembre sin extraer filas de datos. |
| Aceptación | Parcial: continúan la revisión visual, el ensayo con personas y la preparación de entrega. |

### 1.2 Lectura de este documento

Los capítulos principales presentan la propuesta y el funcionamiento transversal. El **anexo A**
incorpora la guía detallada de la base de datos: cada tabla y campo, relaciones, vistas,
disparadores, rutinas y catálogo de consultas. Los estados «implementado», «probado» y
«aceptado por el usuario» se mantienen separados.

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
reconocimiento asistido, historial, sesiones globales, administración, perfil estudiantil,
excepciones y herramientas de operación local. La base está versionada hasta 008.

El login institucional general del estudiante, el envío docente de la contraseña alternativa
por correo, los perfiles de los otros roles, Configuración y el ensayo integral con personas
siguen pendientes. El reconocimiento no incorpora una prueba de presencia real demostrada.

### 4.2 Actores

| Actor | Responsabilidad principal | Restricción relevante |
| --- | --- | --- |
| Docente | Gestionar sus materias, preparar clases y revisar/confirmar asistencia. | Debe ser propietario de la materia y tener cuenta activa. |
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
| RF-12 | Entrega de contraseña alternativa por el profesor mediante correo, similar a ALTA_DOCENTE. | Pendiente; no implementar todavía |
| RF-13 | Login institucional general del estudiante. | Pendiente |

### 4.4 Requisitos de calidad

| Área | Criterio adoptado | Límite actual |
| --- | --- | --- |
| Integridad | PK, FK, CHECK, índices únicos y transacciones. | El propietario Oracle conserva facultades superiores a los roles web. |
| Acceso | Identidad validada, permiso por rol, sesión revocable y caducidad. | Falta completar la separación entre propietario y ejecución para todos los roles. |
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
| Reglas Oracle | sql y sql/migraciones | Estructura, paquetes, triggers, vistas y verificación. |

### 5.2 Decisiones relevantes

- Las reglas sensibles se comprueban en servidor; un botón deshabilitado no es el control definitivo.
- Las conexiones del pool limpian contexto para no heredar el actor de una operación anterior.
- La sesión web y la conexión Oracle son conceptos diferentes.
- Una propuesta biométrica se revisa antes de persistir la confirmación de una clase.
- Una operación de escritura con resultado incierto no se repite indiscriminadamente.
- Las vistas simplifican consultas; el control de filas por usuario depende del contexto y los servicios.

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

### 6.6 Perfil académico

Mi perfil muestra identidad resumida, porcentaje acumulado, materias matriculadas, asistencias,
ausencias y calendario mensual. El porcentaje global se obtiene de registros confirmados,
no del promedio simple de porcentajes por materia. El calendario utiliza el día de clase en
America/Bogota y permite días mixtos si existen resultados distintos entre materias.

La consulta obtiene el estudiante desde la sesión, sin permitir elegir otra cuenta mediante
parámetros de URL. Los perfiles de docente/administrador y Configuración siguen reservados.

### 6.7 Administración

El administrador consulta/exporta auditoría y edita cuentas o materias con motivo y versión
de edición. Una versión obsoleta se rechaza. La conexión técnica utiliza paquetes autorizados
y vistas de historial; no ofrece modificación o borrado de auditoría desde la interfaz.

### 6.8 Excepción biométrica

El administrador comprueba el documento por el procedimiento institucional, concede una
autorización con categoría, referencia y vigencia, y establece una contraseña alternativa.
El estudiante entra con tipo/número de documento y contraseña. La falta de muestras no impide
ese flujo autorizado, disponible sin activar la cámara.

La autorización y el último resultado son datos separados. El acceso alternativo queda marcado
EXCEPCIONAL; no se presenta como una verificación facial. La revocación, el vencimiento o un
cambio de credencial impiden aprovechar pruebas anteriores. Entrar por excepción no marca asistencia.

**Requisito futuro:** la contraseña será proporcionada por el profesor mediante correo, con
dinámica similar a ALTA_DOCENTE. Esa entrega está documentada, no implementada. El flujo vigente
continúa siendo el de autorización administrativa descrito arriba.

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

Los siete paquetes son PKG_AUDITORIA, PKG_ASISTENCIA, PKG_GESTION, PKG_CLASES,
PKG_ADMINISTRACION, PKG_SESIONES y PKG_EXCEPCIONES. Sus especificaciones contienen 35 rutinas
públicas. Validan contexto, propiedad, actividad, motivos, confirmación y sesión según el caso.

Los diez triggers actualizan fechas/versiones, protegen identidad de clases/resultados,
exigen actividad y crean historiales. No son tareas programadas. Los eventos de acceso y
excepción se escriben desde servicios/paquetes; no existe un trigger general para todo el SQL.
La transacción pertenece al llamador: los historiales se confirman o revierten con la acción.

### 7.4 Evolución y visualización

Las versiones 001–008 incorporan estructura inicial, auditoría, clases, estados de detección,
gestión, administración, sesiones y excepciones. `oracle_scripts.sql` conduce a la instalación;
los datos activos permanecen en Oracle. SQL*Plus y SQL Developer son clientes del mismo servicio.

El diccionario existente o el DDL consolidado permiten construir un modelo relacional en
Data Modeler. La importación para dibujar no ejecuta por sí misma una instalación. En la revisión
local se preparó `exports/modelo_008.sql`, sin filas de usuarios; el anexo A explica su uso.

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
frente al propietario Oracle. La separación completa de cuentas de ejecución, retención y
operación institucional requiere trabajo adicional antes de una entrega real.

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
Los créditos nominales del pie aún contienen valores provisionales que deben completarse.

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

## 11. Verificación y evidencias

### 11.1 Estrategia

La verificación combina pruebas de servicios, interfaz y Oracle, datos sintéticos, revisión
de navegador y ensayo de recuperación aislado. Las pruebas automáticas comprueban reglas de
software; no sustituyen la evaluación biométrica con personas ni la aceptación institucional.

| Área | Evidencia registrada | Interpretación |
| --- | --- | --- |
| Publicación completa | 217 pruebas aprobadas con Oracle sobre una copia de los archivos publicables. | Verificación del software de esa entrega. |
| Excepciones | Credenciales incorrectas, bloqueo, revocación, vencimiento, prueba obsoleta y alta sin biometría. | El permiso y la prueba se vuelven a validar en servidor. |
| Navegador | 12 vistas nuevas y 12 anónimas de la instancia HTTPS en la entrega 008. | Revisión de presentación/recorridos, no aceptación global del usuario. |
| Restauración | Dos esquemas temporales, 14 tablas, versiones 001–008 y estados excepcionales recuperados. | Ensayo controlado; los esquemas temporales se retiraron. |
| Consulta estructural | 43 SELECT validados, cero filas de usuarios extraídas, 122 enlaces revisados. | Revisión documental del 18 de noviembre de 2026. |
| Estado Oracle | Cero errores de compilación y cero objetos inválidos en esa consulta. | Coherencia estructural observada, no garantía de operación en cualquier equipo. |

### 11.2 Aceptación y criterios de cierre

Una función puede estar implementada y probada sin haber sido aceptada por el usuario. El cierre
requiere comprobar el recorrido previsto, mensajes, permisos, resultado persistido y recuperación
ante fallos, además de la conformidad visual cuando corresponda.

Para el ensayo final se prevé incluir cámara/micrófono, desconocidos y muestras ausentes,
varias pestañas y dispositivos, QR/LAN, revocación, exportación, copias y restauración.
La calibración debe separar sus muestras de las de evaluación y registrar FAR, FRR y confusiones
solo cuando existan grupos de datos suficientes. No se declara una precisión biométrica medida.

## 12. Roadmap, riesgos y continuidad

### 12.1 Trabajo pendiente

| Bloque | Trabajo siguiente | Dependencia de cierre |
| --- | --- | --- |
| Frontend | Continuar aceptación de navegación, selectores, perfil, pie y zoom. | Revisión expresa de los recorridos por el usuario. |
| Acceso estudiantil | Diseñar login institucional general y recuperación. | Definir el flujo sin sustituir identidad por un formulario anónimo. |
| Entrega alternativa | Contraseña proporcionada por el docente mediante correo, similar a ALTA_DOCENTE. | Aplazado por instrucción del usuario; no implementarlo aún. |
| Perfiles | Mi perfil para otros roles y Configuración. | Definición y autorización de funciones. |
| Entrega por equipo | Portabilidad, dependencias, licencia y separación de ejecución/propietario. | Verificación en otro PC y decisiones operativas. |
| Ensayo real | Personas, dispositivos, biometría, ruido, red y calibración. | Muestras y procedimientos consentidos, métricas y depuración. |
| Presentación de datos | Importación visual en SQL Developer y demostración final. | Revisar el modelo/guion sobre el mismo esquema Oracle. |

### 12.2 Riesgos y tratamiento propuesto

| Riesgo | Consecuencia | Tratamiento actual o pendiente |
| --- | --- | --- |
| Captura deficiente o reproducción de muestras | Identificación errónea o rechazo. | Validación básica y revisión; presencia real/calibración pendientes. |
| Confundir sin muestra con ausencia | Decisión académica incorrecta. | Estados separados y motivo manual obligatorio. |
| Concurrencia o reintentos | Duplicados o cambios parciales. | PK/UNIQUE, bloqueos, versiones e idempotencia. |
| Pérdida de claves privadas | Imposibilidad de recuperar copias o resolver documentos HMAC. | Custodia privada e independiente y ensayo de recuperación. |
| Exceso de privilegios del runtime | Mayor impacto de una credencial comprometida. | Conexión administrativa limitada; completar separación de otros roles. |
| Suposiciones de portabilidad o precisión | Entrega que no reproduce lo prometido. | Documentar el entorno verificado y ensayar otras condiciones. |
| Datos provisionales de presentación | Documento o interfaz con créditos incompletos. | Completar nombres y validar contenidos antes de la entrega formal. |

### 12.3 Criterio de continuidad

El siguiente trabajo debe respetar la separación entre cambios visuales, autenticación,
reglas académicas y operación Oracle. Cada entrega se documenta con alcance, archivos,
verificación y pendientes. La evolución de la base se realiza con migraciones y respaldo
previo; estudiar el modelo o imprimir este documento no requiere aplicar DDL.

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
| docs/BASE_DE_DATOS.md | Inventario estructural y funcionamiento detallado; incorporado en el anexo A. |
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

Los scripts, repositorios y paquetes son la referencia ejecutable del funcionamiento. La
consulta estructural del 18 de noviembre contrastó el esquema instalado con sus fuentes.
La documentación conserva evidencias locales de pruebas; esas evidencias y los secretos no
se incorporan a este PDF. Los archivos de configuración públicos contienen ejemplos, no valores reales.

### 13.3 Recursos institucionales y bibliografía técnica

El logotipo y sus proporciones proceden del Manual de Identidad Visual UPC de 2010, disponible
en Proyecto_recursos. Su procedencia se detalla en static/img/upc/README.md. No se creó un símbolo
universitario alternativo. La captura corresponde a la portada local de la aplicación, sin sesión iniciada.

- Universidad Popular del Cesar. Manual de Identidad Visual, 2010. Recurso local del proyecto.
- Oracle. Data Modeler Concepts and Usage, 24.3. Importación desde DDL y diccionario.
- Oracle. SQL Developer Concepts and Usage, 18.3. Integración de Data Modeler.
- Oracle. Database Installation Guide for Microsoft Windows, 18c. Tablespaces y archivos de datos.

Las referencias web completas aparecen junto a los procedimientos correspondientes del anexo A.
Las rutas de código de esta memoria son relativas a la raíz del repositorio ControlAsistenciaUPC.
