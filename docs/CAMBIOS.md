# Registro de cambios de UPC | Aula

Este archivo resume las entregas y enlaza su documentación. Para localizar todas las guías,
consultar el [índice](README.md); para trabajo pendiente, el [roadmap](ROADMAP.md).
Los resultados indicados corresponden a las verificaciones registradas en cada entrega.

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
