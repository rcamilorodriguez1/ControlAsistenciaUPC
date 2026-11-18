# Registro de cambios de UPC | Aula

Este archivo resume las entregas y enlaza su documentación. Para localizar todas las guías,
consultar el [índice](README.md); para trabajo pendiente, el [roadmap](ROADMAP.md).
Los resultados indicados corresponden a las verificaciones registradas en cada entrega.

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
